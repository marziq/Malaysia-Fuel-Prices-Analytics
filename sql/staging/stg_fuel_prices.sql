CREATE OR REPLACE TABLE
    `malaysia-fuel-analytics.staging.stg_fuel_prices`
AS

SELECT
    SAFE_CAST(date AS DATE) AS fuel_date,

    SAFE_CAST(ron95 AS FLOAT64) AS ron95_price,
    SAFE_CAST(ron97 AS FLOAT64) AS ron97_price,
    SAFE_CAST(diesel AS FLOAT64) AS diesel_price

FROM
    `malaysia-fuel-analytics.raw.fuel_prices`

WHERE
    SAFE_CAST(date AS DATE) IS NOT NULL;