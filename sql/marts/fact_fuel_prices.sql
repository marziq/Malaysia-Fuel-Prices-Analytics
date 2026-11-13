CREATE OR REPLACE TABLE
    `malaysia-fuel-analytics.mart.fact_fuel_prices`
AS

SELECT
    fuel_date,
    ron95_price,
    ron97_price,
    diesel_price,

    EXTRACT(YEAR FROM fuel_date) AS year,
    EXTRACT(MONTH FROM fuel_date) AS month,
    FORMAT_DATE('%B', fuel_date) AS month_name,
    EXTRACT(QUARTER FROM fuel_date) AS quarter

FROM
    `malaysia-fuel-analytics.staging.stg_fuel_prices`;

SELECT
    year,
    month_name,
    COUNT(*) AS total_records,
    AVG(ron95_price) AS average_ron95,
    AVG(ron97_price) AS average_ron97,
    AVG(diesel_price) AS average_diesel
FROM
    `malaysia-fuel-analytics.mart.fact_fuel_prices`
GROUP BY
    year,
    month,
    month_name
ORDER BY
    year,
    month;