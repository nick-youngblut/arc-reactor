from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from backend.agents.tools.base import (
    compute_date_range,
    ensure_limit,
    format_fastq_paths,
    format_ngs_run_results,
    format_qc_summary,
    format_run_samples_result,
    format_table,
    get_tool_context,
    parse_semicolon_delimited,
    q30_status,
    tool_error_handler,
)


@tool
@tool_error_handler
async def search_ngs_runs(
    ngs_run: str | None = None,
    pooled_sample: str | None = None,
    submitter: str | None = None,
    submitter_email: str | None = None,
    instrument: str | None = None,
    platform: str | None = None,
    project: str | None = None,
    lib_prep_method: str | None = None,
    cost_center: str | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
    days_back: int | None = None,
    use_wildcards: bool = False,
    include_qc_summary: bool = False,
    limit: int | None = None,
    runtime: Any | None = None,
) -> str:
    """
    Search for NGS runs with flexible filtering options.

    Args:
        ngs_run: NGS Run name (e.g., "NR-2024-0156") or pattern with wildcards
        pooled_sample: Pooled sample / SspArc name (e.g., "SspArc0050")
        submitter: Submitter name
        submitter_email: Submitter email address
        instrument: Instrument name (NovaSeqX, NextSeq2000, etc.)
        project: Project name
        lib_prep_method: Library prep method
        cost_center: Cost center for billing
        start_date: Start of date range (YYYY-MM-DD)
        end_date: End of date range (YYYY-MM-DD)
        days_back: Alternative to date range - last N days
        use_wildcards: Treat names as SQL wildcard patterns (%, _)
        limit: Maximum results to return (default: 50, max: 500)
        include_qc_summary: Include basic QC metrics (slower query)

    Returns:
        Toon formatted table of matching NGS runs with key metadata
    """
    context = get_tool_context(runtime)
    benchling = context.benchling

    conditions = ['nr."archived$" = FALSE']
    params: dict[str, Any] = {}

    start_date, end_date = compute_date_range(
        days_back=days_back,
        start_date=start_date,
        end_date=end_date,
        min_date=min_date,
        max_date=max_date,
    )

    if start_date:
        conditions.append("nro.completion_date >= :start_date")
        params["start_date"] = start_date

    if end_date:
        conditions.append("nro.completion_date <= :end_date")
        params["end_date"] = end_date

    op = "LIKE" if use_wildcards else "="

    if ngs_run:
        conditions.append(f'nr."name$" {op} :ngs_run')
        params["ngs_run"] = ngs_run

    if pooled_sample:
        conditions.append(f'ps."name$" {op} :pooled_sample')
        params["pooled_sample"] = pooled_sample

    if submitter:
        conditions.append(
            """
            (ps.submitter_first_name ILIKE :submitter_pattern
             OR ps.submitter_last_name ILIKE :submitter_pattern
             OR CONCAT(ps.submitter_first_name, ' ', ps.submitter_last_name) ILIKE :submitter_pattern)
            """
        )
        params["submitter_pattern"] = f"%{submitter}%"

    if submitter_email:
        conditions.append("ps.submitter_email = :submitter_email")
        params["submitter_email"] = submitter_email

    effective_instrument = instrument or platform
    if effective_instrument:
        conditions.append(f'ni."name$" {op} :instrument')
        params["instrument"] = effective_instrument

    if project:
        conditions.append(f'pt."name$" {op} :project')
        params["project"] = project

    if lib_prep_method:
        conditions.append("lps.lib_prep_method = :lib_prep_method")
        params["lib_prep_method"] = lib_prep_method

    if cost_center:
        conditions.append("ps.cost_center = :cost_center")
        params["cost_center"] = cost_center

    if status:
        conditions.append("nro.status = :status")
        params["status"] = status

    where_clause = " AND ".join(conditions)

    qc_columns = ""
    qc_join = ""
    if include_qc_summary:
        qc_columns = """,
            AVG(nros.q30_percent) AS avg_q30,
            SUM(nros.sequenced_number_of_molecules) AS total_reads
        """
        qc_join = "LEFT JOIN ngs_run_output_sample$raw nros ON nr.id = nros.ngs_run"

    sql = f"""
    SELECT DISTINCT
        nr."name$" AS ngs_run,
        ps."name$" AS pooled_sample,
        CONCAT(ps.submitter_first_name, ' ', ps.submitter_last_name) AS submitter,
        ni."name$" AS instrument,
        nro.completion_date,
        COUNT(DISTINCT lps."name$") AS sample_count,
        nro.link_to_sequencing_data AS run_path
        {qc_columns}
    FROM ngs_run$raw nr
    INNER JOIN ngs_instrument$raw ni ON nr.instrument = ni.id
    INNER JOIN ngs_run_output_v2$raw nro ON nr.id = nro.ngs_run
    INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
    INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
    LEFT JOIN ngs_library_pooling_v2$raw nlp ON ps.id = nlp.destination
    LEFT JOIN library_prep_sample$raw lps ON nlp.source = lps.id
    LEFT JOIN project_tag$raw pt ON lps.project = pt.id
    {qc_join}
    WHERE {where_clause}
        AND ni."archived$" = FALSE
        AND nro."archived$" = FALSE
        AND (ps."archived$" = FALSE OR ps."archived$" IS NULL)
        AND (lps."archived$" = FALSE OR lps."archived$" IS NULL)
    GROUP BY
        nr."name$", ps."name$", ps.submitter_first_name, ps.submitter_last_name,
        ni."name$", nro.completion_date, nro.link_to_sequencing_data
    ORDER BY nro.completion_date DESC
    LIMIT :limit
    """

    params["limit"] = ensure_limit(limit)

    rows = await benchling.query(sql, params, return_format="dict")
    return format_ngs_run_results(rows)


@tool
@tool_error_handler
async def get_ngs_run_samples(
    ngs_run: str | None = None,
    pooled_sample: str | None = None,
    include_fastq_paths: bool = True,
    include_metadata: bool = True,
    include_qc: bool = True,
    limit: int | None = None,
    runtime: Any | None = None,
) -> str:
    """
    Get detailed sample information for a specific NGS run.

    Args:
        ngs_run: NGS Run name (e.g., "NR-2024-0156")
        pooled_sample: Pooled sample / SspArc name (e.g., "SspArc0050")
        include_fastq_paths: Include FASTQ file paths
        include_metadata: Include sample metadata
        include_qc: Include per-sample QC metrics
        limit: Maximum results to return (default: 100, max: 1000)
        runtime: LangChain tool runtime for injected services/config.

    Returns:
        Toon formatted table of sample information
    """
    if not ngs_run and not pooled_sample:
        return "Error: Please provide either ngs_run or pooled_sample parameter."

    context = get_tool_context(runtime)
    benchling = context.benchling

    if ngs_run:
        run_filter = 'nr."name$" = :run_id'
        params: dict[str, Any] = {"run_id": ngs_run}
    else:
        run_filter = 'ps."name$" = :pooled_sample'
        params = {"pooled_sample": pooled_sample}

    metadata_cols = ""
    metadata_join = ""
    if include_metadata:
        metadata_cols = """,
            md.organism,
            md.tissue,
            md.cell_line,
            md.perturbation,
            md.replicate
        """
        metadata_join = """
        LEFT JOIN ngs_library_metadata_v2$raw md
            ON lps.id = md.ngs_library AND md."archived$" = FALSE
        """

    qc_cols = ""
    qc_join = ""
    if include_qc:
        qc_cols = """,
            nros.sequenced_number_of_molecules AS read_count,
            nros.q30_percent,
            nros.average_read_length
        """
        qc_join = "LEFT JOIN ngs_run_output_sample$raw nros ON nr.id = nros.ngs_run AND lps.id = nros.ngs_library AND nros.read = 'R1'"

    fastq_cols = ""
    fastq_join = ""
    if include_fastq_paths:
        fastq_cols = """,
            nros_r1.link_to_fastq_file AS fastq_r1,
            nros_r2.link_to_fastq_file AS fastq_r2
        """
        fastq_join = """
        LEFT JOIN ngs_run_output_sample$raw nros_r1
            ON nr.id = nros_r1.ngs_run
            AND lps.id = nros_r1.ngs_library
            AND nros_r1.read = 'R1'
            AND nros_r1."archived$" = FALSE
        LEFT JOIN ngs_run_output_sample$raw nros_r2
            ON nr.id = nros_r2.ngs_run
            AND lps.id = nros_r2.ngs_library
            AND nros_r2.read = 'R2'
            AND nros_r2."archived$" = FALSE
        """

    sql = f"""
    WITH run_info AS (
        SELECT DISTINCT
            nr."name$" AS ngs_run,
            ps."name$" AS pooled_sample,
            ps.submitter_first_name,
            ps.submitter_last_name,
            ps.submitter_email,
            ps.cost_center,
            ni."name$" AS instrument,
            nro.completion_date,
            nro.link_to_sequencing_data AS run_path
        FROM ngs_run$raw nr
        INNER JOIN ngs_instrument$raw ni ON nr.instrument = ni.id
        INNER JOIN ngs_run_output_v2$raw nro ON nr.id = nro.ngs_run
        INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
        INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
        WHERE {run_filter}
            AND nr."archived$" = FALSE
            AND ni."archived$" = FALSE
            AND nro."archived$" = FALSE
            AND (ps."archived$" = FALSE OR ps."archived$" IS NULL)
        LIMIT 1
    ),
    samples AS (
        SELECT DISTINCT
            lps.sample_id,
            lps."name$" AS sample_name,
            lps.lib_prep_method,
            lps.lib_prep_kit_used
            {fastq_cols}
            {metadata_cols}
            {qc_cols}
        FROM ngs_run$raw nr
        INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
        INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
        INNER JOIN ngs_library_pooling_v2$raw nlp ON ps.id = nlp.destination
        INNER JOIN library_prep_sample$raw lps ON nlp.source = lps.id
        {fastq_join}
        {qc_join}
        {metadata_join}
        WHERE {run_filter}
            AND nr."archived$" = FALSE
            AND lps."archived$" = FALSE
            AND (ps."archived$" = FALSE OR ps."archived$" IS NULL)
        ORDER BY lps.sample_id
        LIMIT :limit
    )
    SELECT * FROM run_info, samples
    """

    params["limit"] = ensure_limit(limit, default=100)

    rows = await benchling.query(sql, params, return_format="dict")
    if not rows:
        return "No samples found for the requested run."

    first = rows[0]
    summary = {
        "ngs_run": first.get("ngs_run"),
        "pooled_sample": first.get("pooled_sample"),
        "submitter": " ".join(
            [
                str(first.get("submitter_first_name") or ""),
                str(first.get("submitter_last_name") or ""),
            ]
        ).strip(),
        "instrument": first.get("instrument"),
        "completion_date": first.get("completion_date"),
        "sample_count": len(rows),
        "run_path": first.get("run_path"),
    }

    exclude_keys = {
        "ngs_run",
        "pooled_sample",
        "submitter_first_name",
        "submitter_last_name",
        "submitter_email",
        "cost_center",
        "instrument",
        "completion_date",
        "run_path",
    }
    samples = [{k: v for k, v in row.items() if k not in exclude_keys} for row in rows]

    return format_run_samples_result(summary, samples)


@tool
@tool_error_handler
async def get_ngs_run_qc(
    ngs_run: str | None = None,
    pooled_sample: str | None = None,
    level: str = "summary",
    runtime: Any | None = None,
) -> str:
    """
    Get QC metrics for an NGS run.

    Args:
        ngs_run: NGS Run name (e.g., "NR-2024-0156")
        pooled_sample: Pooled sample / SspArc name (e.g., "SspArc0050")
        level: Detail level - "summary", "lane", or "sample" (default: "summary")
        runtime: LangChain tool runtime for injected services/config.

    Returns:
        String message containing the QC metrics
    """
    if not ngs_run and not pooled_sample:
        return "Error: Please provide either ngs_run or pooled_sample parameter."

    context = get_tool_context(runtime)
    benchling = context.benchling

    if ngs_run:
        run_filter = 'nr."name$" = :run_id'
        params: dict[str, Any] = {"run_id": ngs_run}
    else:
        run_filter = 'ps."name$" = :pooled_sample'
        params = {"pooled_sample": pooled_sample}

    normalized = (level or "summary").lower()

    if normalized == "summary":
        summary_sql = f"""
        SELECT
            nr."name$" AS ngs_run,
            ps."name$" AS pooled_sample,
            ni."name$" AS instrument,
            nro.completion_date,
            COUNT(DISTINCT lps.id) AS sample_count,
            SUM(nros.sequenced_number_of_molecules) AS total_reads,
            AVG(nros.q30_percent) AS avg_q30,
            AVG(nros.average_read_length) AS avg_read_length
        FROM ngs_run$raw nr
        INNER JOIN ngs_instrument$raw ni ON nr.instrument = ni.id
        INNER JOIN ngs_run_output_v2$raw nro ON nr.id = nro.ngs_run
        INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
        INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
        INNER JOIN ngs_library_pooling_v2$raw nlp ON ps.id = nlp.destination
        INNER JOIN library_prep_sample$raw lps ON nlp.source = lps.id
        LEFT JOIN ngs_run_output_sample$raw nros ON nr.id = nros.ngs_run
        WHERE {run_filter}
            AND nr."archived$" = FALSE
            AND ni."archived$" = FALSE
            AND nro."archived$" = FALSE
            AND (ps."archived$" = FALSE OR ps."archived$" IS NULL)
        GROUP BY
            nr."name$", ps."name$", ni."name$", nro.completion_date
        """
        summary_rows = await benchling.query(summary_sql, params, return_format="dict")
        if not summary_rows:
            return "No QC data found for the requested run."
        summary = summary_rows[0]
        avg_q30 = summary.get("avg_q30")
        summary["qc_status"] = q30_status(avg_q30)

        lane_sql = f"""
        SELECT
            nrod.lane AS lane,
            SUM(nrod.reads_millions) AS reads,
            AVG(nrod.percent_q30) AS avg_q30,
            AVG(nrod.error_rate) AS error_rate
        FROM ngs_run$raw nr
        INNER JOIN ngs_run_output_v2$raw nro ON nr.id = nro.ngs_run
        INNER JOIN ngs_run_output_detailed nrod ON nr.id = nrod.ngs_run
        INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
        INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
        WHERE {run_filter}
            AND nr."archived$" = FALSE
            AND nro."archived$" = FALSE
            AND nrod."archived$" = FALSE
        GROUP BY nrod.lane
        ORDER BY nrod.lane
        """
        lane_rows = await benchling.query(lane_sql, params, return_format="dict")
        for lane in lane_rows:
            lane["status"] = q30_status(lane.get("avg_q30"))
        return format_qc_summary(summary, lane_rows)

    if normalized == "lane":
        sql = f"""
        SELECT
            nrod.lane AS lane,
            nrod.read AS read,
            AVG(nrod.percent_q30) AS avg_q30,
            SUM(nrod.reads_millions) AS reads_millions,
            AVG(nrod.error_rate) AS error_rate
        FROM ngs_run$raw nr
        INNER JOIN ngs_run_output_v2$raw nro ON nr.id = nro.ngs_run
        INNER JOIN ngs_run_output_detailed nrod ON nr.id = nrod.ngs_run
        INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
        INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
        WHERE {run_filter}
            AND nr."archived$" = FALSE
            AND nro."archived$" = FALSE
            AND nrod."archived$" = FALSE
        GROUP BY nrod.lane, nrod.read
        ORDER BY nrod.lane, nrod.read
        """
        rows = await benchling.query(sql, params, return_format="dict")
        for row in rows:
            row["status"] = q30_status(row.get("avg_q30"))
        return format_table(rows)

    if normalized == "sample":
        sql = f"""
        SELECT
            lps.sample_id,
            SUM(nros.sequenced_number_of_molecules) AS total_reads,
            AVG(nros.q30_percent) AS avg_q30,
            AVG(nros.average_read_length) AS avg_read_length
        FROM ngs_run$raw nr
        INNER JOIN ngs_run_pooling_v2$raw nrp ON nr.id = nrp.ngs_run
        INNER JOIN pooled_sample$raw ps ON nrp.ngs_library_pool = ps.id
        INNER JOIN ngs_library_pooling_v2$raw nlp ON ps.id = nlp.destination
        INNER JOIN library_prep_sample$raw lps ON nlp.source = lps.id
        LEFT JOIN ngs_run_output_sample$raw nros
            ON nr.id = nros.ngs_run
            AND lps.id = nros.ngs_library
        WHERE {run_filter}
            AND nr."archived$" = FALSE
            AND (ps."archived$" = FALSE OR ps."archived$" IS NULL)
            AND (lps."archived$" = FALSE OR lps."archived$" IS NULL)
        GROUP BY lps.sample_id
        ORDER BY lps.sample_id
        """
        rows = await benchling.query(sql, params, return_format="dict")
        for row in rows:
            row["status"] = q30_status(row.get("avg_q30"))
        return format_table(rows)

    return "Error: Invalid level. Use 'summary', 'lane', or 'sample'."


@tool
@tool_error_handler
async def get_fastq_paths(
    sample_names: str | None = None,
    sample_ids: str | None = None,
    ngs_run: str | None = None,
    pooled_sample: str | None = None,
    verify_exists: bool = False,
    runtime: Any | None = None,
) -> str:
    """
    Get FASTQ file paths for specified samples.

    Args:
        sample_names: Sample names, semicolon-delimited (e.g., "LPS-001;LPS-002")
        sample_ids: Sample IDs, semicolon-delimited (e.g., "LPS-001;LPS-002")
        ngs_run: NGS Run name (e.g., "NR-2024-0156")
        pooled_sample: Pooled sample / SspArc name (e.g., "SspArc0050")
        verify_exists: Check if files exist in GCS (default: false)
        runtime: LangChain tool runtime for injected services/config.

    Returns:
        Toon formatted table of FASTQ file paths
    """
    identifiers = sample_names or sample_ids
    samples = parse_semicolon_delimited(identifiers)
    if not samples:
        return "Error: sample_names or sample_ids must be provided."

    context = get_tool_context(runtime)
    benchling = context.benchling

    sample_params = {f"s{i}": s for i, s in enumerate(samples)}
    sample_placeholders = ", ".join(f":s{i}" for i in range(len(samples)))

    run_filter = ""
    if ngs_run:
        run_filter = 'AND nr."name$" = :ngs_run'
        sample_params["ngs_run"] = ngs_run
    elif pooled_sample:
        run_filter = 'AND ps."name$" = :pooled_sample'
        sample_params["pooled_sample"] = pooled_sample

    sql = f"""
    SELECT DISTINCT
        lps.sample_id,
        nr."name$" AS ngs_run,
        nros_r1.link_to_fastq_file AS fastq_r1,
        nros_r2.link_to_fastq_file AS fastq_r2
    FROM library_prep_sample$raw lps
    INNER JOIN ngs_library_pooling_v2$raw nlp ON lps.id = nlp.source
    INNER JOIN pooled_sample$raw ps ON nlp.destination = ps.id
    INNER JOIN ngs_run_pooling_v2$raw nrp ON ps.id = nrp.ngs_library_pool
    INNER JOIN ngs_run$raw nr ON nrp.ngs_run = nr.id
    LEFT JOIN ngs_run_output_sample$raw nros_r1
        ON nr.id = nros_r1.ngs_run
        AND lps.id = nros_r1.ngs_library
        AND nros_r1.read = 'R1'
    LEFT JOIN ngs_run_output_sample$raw nros_r2
        ON nr.id = nros_r2.ngs_run
        AND lps.id = nros_r2.ngs_library
        AND nros_r2.read = 'R2'
    WHERE lps.sample_id IN ({sample_placeholders})
        AND lps."archived$" = FALSE
        AND nr."archived$" = FALSE
        {run_filter}
    ORDER BY lps.sample_id
    """

    rows = await benchling.query(sql, sample_params, return_format="dict")

    if verify_exists and context.storage is not None:
        paths: list[str] = []
        for row in rows:
            if row.get("fastq_r1"):
                paths.append(row["fastq_r1"])
            if row.get("fastq_r2"):
                paths.append(row["fastq_r2"])
        existence = context.storage.files_exist(paths)
        for row in rows:
            r1 = row.get("fastq_r1")
            r2 = row.get("fastq_r2")
            checks = [
                existence.get(r1, False) if r1 else False,
                existence.get(r2, False) if r2 else False,
            ]
            row["exists"] = "YES" if all(checks) else "NO"

    return format_fastq_paths(rows, validated=verify_exists)
