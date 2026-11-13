
CREATE OR REPLACE TABLE
    `malaysia-fuel-analytics.mart.fact_exchange_rates`
AS

SELECT
    currency_code,
    unit,
    rate_date,

    buying_rate,
    selling_rate,
    middle_rate,

    EXTRACT(YEAR FROM rate_date) AS year,

    EXTRACT(QUARTER FROM rate_date) AS quarter,

    EXTRACT(MONTH FROM rate_date) AS month,

    FORMAT_DATE('%B', rate_date) AS month_name,

    FORMAT_DATE('%Y-%m', rate_date) AS year_month

FROM
    `malaysia-fuel-analytics.staging.stg_exchange_rates`

WHERE
    rate_date IS NOT NULL;
