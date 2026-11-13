
CREATE OR REPLACE TABLE
    `malaysia-fuel-analytics.mart.fact_crude_oil`
AS

SELECT
    observation_date,

    area_code,
    area_name,

    product_code,
    product_name,

    process_code,
    process_name,

    series_code,
    series_description,

    crude_oil_price,
    price_unit,

    EXTRACT(YEAR FROM observation_date) AS year,

    EXTRACT(QUARTER FROM observation_date) AS quarter,

    EXTRACT(MONTH FROM observation_date) AS month,

    FORMAT_DATE('%B', observation_date) AS month_name,

    FORMAT_DATE('%Y-%m', observation_date) AS year_month

FROM
    `malaysia-fuel-analytics.staging.stg_crude_oil`

WHERE
    observation_date IS NOT NULL
    AND crude_oil_price IS NOT NULL;
