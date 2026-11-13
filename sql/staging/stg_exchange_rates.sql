
CREATE OR REPLACE TABLE
    `malaysia-fuel-analytics.staging.stg_exchange_rates`
AS

SELECT
    UPPER(TRIM(currency_code)) AS currency_code,

    SAFE_CAST(unit AS INT64) AS unit,

    SAFE_CAST(rate_date AS DATE) AS rate_date,

    SAFE_CAST(rate_buying_rate AS FLOAT64)
        AS buying_rate,

    SAFE_CAST(rate_selling_rate AS FLOAT64)
        AS selling_rate,

    SAFE_CAST(rate_middle_rate AS FLOAT64)
        AS middle_rate

FROM
    `malaysia-fuel-analytics.raw.exchange_rates`

WHERE
    SAFE_CAST(rate_date AS DATE) IS NOT NULL
    AND currency_code IS NOT NULL
    AND TRIM(currency_code) != '';
