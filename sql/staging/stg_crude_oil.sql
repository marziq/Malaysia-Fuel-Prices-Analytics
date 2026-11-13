
CREATE OR REPLACE TABLE
    `malaysia-fuel-analytics.staging.stg_crude_oil`
AS

SELECT
    SAFE_CAST(period AS DATE) AS observation_date,

    TRIM(duoarea) AS area_code,
    TRIM(area_name) AS area_name,

    TRIM(product) AS product_code,
    TRIM(product_name) AS product_name,

    TRIM(process) AS process_code,
    TRIM(process_name) AS process_name,

    TRIM(series) AS series_code,
    TRIM(series_description) AS series_description,

    SAFE_CAST(value AS FLOAT64) AS crude_oil_price,

    TRIM(units) AS price_unit

FROM
    `malaysia-fuel-analytics.raw.crude_oil`

WHERE
    SAFE_CAST(period AS DATE) IS NOT NULL
    AND SAFE_CAST(value AS FLOAT64) IS NOT NULL;
