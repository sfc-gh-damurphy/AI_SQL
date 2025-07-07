# AI SQL: HOL Setup

This lab introduces a new era for SQL analytics, bridging the gap between analysts and AI engineer capabilities. By leveraging SQL with AI-powered operators in Snowflake, analysts can easily access and analyze multimodal data at scale. The solution combines simple SQL syntax with high-performance processing at a lower cost, delivering trusted insights across the enterprise.

## What you’ll do:

It is recommended to download this document from Compass and run it from your GDrive to facilitate easier copying and pasting, avoiding formatting issues that can occur when copying directly from Compass.

This lab will explore AI SQL through two different examples.

### Part 1: Equity Research Data

The first example focuses on equity research data. This involves using Snowflake Marketplace for common S\&P 500 stock tickers and documents containing press releases from various organizations about their company initiatives. These two data sources will be combined with AI SQL to gain insights from both structured and unstructured data, insights previously only available to AI Engineers but now easily accessible by analysts.

**Outline of Part 1:**

  * Ingest text data related to stock market information
  * Ingest PDF documents and parse them into a table for analysis by Cortex
  * Filter data using AI SQL
  * Aggregate data using AI SQL
  * Summarize data using AI SQL

### Part 2: Restaurant Reviews and Menu Items

The second part of the lab will examine restaurant reviews and pictures of menu items. This data will be aggregated to draw conclusions about reviews available on Doordash. AI will also be used to join restaurant images with text data for multimodal analysis in a single place.

**Outline of Part 2:**

  * Ingest text data related to DoorDash reviews
  * Ingest Images and generate descriptions using Cortex to analyze the images
  * Filter data using AI SQL
  * Aggregate data using AI SQL
  * Summarize data using AI SQL

## Why this matters:

  * **More Users Leveraging Cortex:** Everyday analysts can be transformed into AI engineers without complex coding.
  * **AI-powered multi-modal data operations:** Unlock powerful capabilities like classification, summarization, extraction, sentiment analysis, translation, audio transcript, and image search, all using SQL queries.
  * **Easily combine AI operations with traditional SQL functions:** JOIN, FILTER, and AGGREGATE can be used to analyze both structured and unstructured data together in a single table, all within Snowflake.
  * **Zero setup needed:** Query structured and unstructured data in a single table with existing SQL knowledge. No new tools or languages are required, democratizing AI across your enterprise, and providing AI-powered insights in minutes, not weeks. There's no model training or complex pipelines; just write your query and go.

## Step 1: Configure DORA for Grading

### Why Use DORA?

  * **Automated Grading:** DORA allows SE BPs to automatically grade hands-on curriculum tasks using the grading framework from the Training team. Developer Relations also utilizes it for event labs.
  * **Functionality:** DORA enables SE BPs to create tests that validate the completion of hands-on steps and track progress towards certification.

### DORA API Integration Setup

Follow the steps below in a new SQL worksheet in your Snowflake account to submit grading requests via external functions.

```sql
USE ROLE ACCOUNTADMIN;

-- Create API integration
CREATE OR REPLACE API INTEGRATION dora_api_integration
API_PROVIDER = AWS_API_GATEWAY
API_AWS_ROLE_ARN = 'arn:aws:iam::321463406630:role/snowflakeLearnerAssumedRole'
ENABLED = TRUE
API_ALLOWED_PREFIXES = (
'https://awy6hshxy4.execute-api.us-west-2.amazonaws.com/dev/edu_dora'
);

-- Confirm integration
SHOW INTEGRATIONS;

-- Create utility database
CREATE OR REPLACE DATABASE util_db;

-- Create greeting function
CREATE OR REPLACE EXTERNAL FUNCTION util_db.public.se_greeting(
email VARCHAR,
firstname VARCHAR,
middlename VARCHAR,
lastname VARCHAR
)
RETURNS VARIANT
API_INTEGRATION = dora_api_integration
CONTEXT_HEADERS = (
CURRENT_TIMESTAMP,
CURRENT_ACCOUNT,
CURRENT_STATEMENT,
CURRENT_ACCOUNT_NAME
)
AS 'https://awy6hshxy4.execute-api.us-west-2.amazonaws.com/dev/edu_dora/greeting';

-- Replace with your Snowflake details
-- Example:
-- SELECT util_db.public.se_greeting(
--   'dan.murphy@snowflake.com', 'Dan', '', 'Murphy');

SELECT util_db.public.se_greeting(
'your_email@snowflake.com',
'Your First Name',
'Your Middle Name or empty string',
'Your Last Name'
);

-- Create grading function
CREATE OR REPLACE EXTERNAL FUNCTION util_db.public.se_grader(
step VARCHAR,
passed BOOLEAN,
actual INTEGER,
expected INTEGER,
description VARCHAR
)
RETURNS VARIANT
API_INTEGRATION = dora_api_integration
CONTEXT_HEADERS = (
CURRENT_TIMESTAMP,
CURRENT_ACCOUNT,
CURRENT_STATEMENT,
CURRENT_ACCOUNT_NAME
)
AS 'https://awy6hshxy4.execute-api.us-west-2.amazonaws.com/dev/edu_dora/grader';

GRANT USAGE ON DATABASE util_db TO ROLE public;
GRANT USAGE ON SCHEMA util_db.public TO ROLE public;
GRANT USAGE ON FUNCTION util_db.public.se_grader(varchar,boolean,integer,integer,varchar) TO ROLE public;
```

**Expected Output:** You should see confirmation messages after each `CREATE` statement and be able to run the `se_greeting` function successfully.

## Step 2: Download Files for the Lab and Upload Them to the Stage

1.  Go to the repository folder for each sections, you can choose to download a zip or download the files individually:
* [Equity Research](/Equity%20Research)
* [Resturant](/Restaurant)
2.  Create Snowflake Stages. Remember to choose server-side encryption for your stage, or follow the code below.
3.  Unzip the files on your machine into separate folders for each lab.
4.  Upload them to the stage or import them through the Snowsight UI.
5.  Log in to your Snowflake demo account.
6.  Create a database for this HOL.

<!-- end list -->

```sql
use role sysadmin;

--Database for lab
Create or Replace DATABASE AISQL_HOL;

--Schema for each part of the lab
Create or Replace SCHEMA AISQL_HOL.EQUITYRESEARCH;
Create or Replace SCHEMA AISQL_HOL.RESTAURANT;

--Stages for files to be uploaded
Create or Replace STAGE AISQL_HOL.EQUITYRESEARCH.EQUITYDOCS ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
Create or Replace STAGE AISQL_HOL.RESTAURANT.FOODIMAGES ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

--create warehouse for lab
create WAREHOUSE IDENTIFIER('"WH_AISQL_HOL"') COMMENT = '' WAREHOUSE_SIZE = 'xsmall' AUTO_RESUME = true AUTO_SUSPEND = 300 ENABLE_QUERY_ACCELERATION = false WAREHOUSE_TYPE = 'STANDARD' MIN_CLUSTER_COUNT = 1 MAX_CLUSTER_COUNT = 1 SCALING_POLICY = 'STANDARD';
```

7.  In the database browser, navigate to the `EQUITYDOCS` stage and upload the 7 PDFs from the `EquitResearch/EquityDOCS` folder you extracted. Ensure you enable directory table to see your files listed.

8.  Repeat the upload process for the `FOODIMAGES` folder. Place these 14 images in the `AISQL_HOL.RESTAURANT.FOODIMAGE` stage you created earlier.

9.  Create the `DOORDASH_100` table from the `DOORDASH_100.CSV` file found in the `Restaurant` zip package. Create this table in the `AISQL_HOL.RESTAURANT` schema using "create table from file" in Snowsight. Leave all defaults to ensure correct table creation.

## Step 3: Bring in the Market Listing for the S\&P 500 Tickers

Open the Snowflake Marketplace listing and import the listing for the S\&P 500. You can leave all the defaults as they are, as this is how they will be referenced in the notebook.

## Step 4: Upload the ipynb file to start Equity Research Lab

Navigate to `Projects` → `Notebooks`, then click `⌄` to `Import ipynb file`. Select the `AISQL Equity Research.ipynb` file from the `EquityResearch` Zip folder. Ensure the notebook location matches the `AISQL_HOL` Database and the `EQUITYRESEARCH` Schema, and choose the `WH_AISQL_HOL` warehouse for both the query warehouse and the notebook warehouse.

## Step 5: Complete Lab using Notebook

The code in the lab contains pseudo-code that needs to be completed for the statements to run. Refer to the header box above the code for links to documentation that will assist in writing the necessary lines of code to complete the exercise.

## Step 6: Validate Using DORA

Run the following commands in Snowsight to confirm your completion of the Equity Lab.

### Validate `RAW_DOCS_TEXT` Table

```sql
use database AISQL_HOL;
use schema EQUITYRESEARCH;

SELECT
util_db.public.se_grader(
step,
(actual = expected),
actual,
expected,
description
) AS graded_results
FROM
(
SELECT
'SEDW10' AS step,
(
SELECT
COUNT(RELATIVE_PATH)
FROM
RAW_DOCS_TEXT
) AS actual,
7 AS expected,
'Docs Loaded and parsed correctly for AISQL Equity Lab' AS description
);
```

### Validate `MATCHED_CANDIDATES` Table (AI\_FILTER)

```sql
use database AISQL_HOL;
use schema EQUITYRESEARCH;

SELECT
util_db.public.se_grader(
step,
(actual = expected),
actual,
expected,
description
) AS graded_results
FROM
(
SELECT
'SEDW11' AS step,
(
SELECT
CASE WHEN COUNT(FILE_NAME) > 2 THEN 1
ELSE 0
END
FROM
MATCHED_CANDIDATES
) AS actual,
1 AS expected,
'AIFILTER successfully applied to AISQL Equity Lab' AS description
);
```

### Validate `AIAGG_RESULTS` Table (AI\_AGG)

```sql
use database AISQL_HOL;
use schema EQUITYRESEARCH;

SELECT
util_db.public.se_grader(
step,
(actual = expected),
actual,
expected,
description
) AS graded_results
FROM
(
SELECT
'SEDW12' AS step,
(
SELECT
COUNT(mapped_ticker)
FROM
AIAGG_Results
) AS actual,
1 AS expected,
'AIAGG successfully applied to AISQL Equity Lab' AS description
);
```

If all 3 validations return ✅, your data is ready for the next step.

## Step 7: Upload the ipynb file to start Restaurant Lab

Navigate to `Projects` → `Notebooks`, then click `⌄` to `Import ipynb file`. Select the `AISQL Restaurant Review.ipynb` file from the `Restaurant` Zip folder. Ensure the notebook location matches the `AISQL_HOL` Database and the `RESTAURANT` Schema, and choose the `WH_AISQL_HOL` warehouse for both the query warehouse and the notebook warehouse. **Make sure to complete this step before running the Notebook\!**

## Step 8: Upload the additional snowbook extras python sheet to the notebook

For this lab, you will need to load an additional file for the notebook. Do this by clicking the `+` sign on the left side and then choosing the `snowbooks_extras.py` file from the zip file you extracted earlier. Confirm that the file is present.

## Step 9: Complete the Lab using the Notebook

The code in the lab contains pseudo-code that needs to be completed for the statements to run. Refer to the header box above the code for links to documentation that will assist in writing the necessary lines of code to complete the exercise.

## Step 10: Validate Using DORA

Run the following commands in Snowsight to confirm your completion of the Restaurant Review Lab.

### Validate `AICLASSIFY_REVIEW` Table

```sql
use database AISQL_HOL;
use schema RESTAURANT;

SELECT
util_db.public.se_grader(
step,
(actual = expected),
actual,
expected,
description
) AS graded_results
FROM
(
SELECT
'SEDW13' AS step,
(
SELECT
COUNT(*)
FROM
AICLASSIFY_REVIEW
) AS actual,
100 AS expected,
'AICLASSIFY successfully applied to AISQL Restaurant' AS description
);
```

### Validate `SUMMARIZEAGG_EXPERIENCE` Table

```sql
use database AISQL_HOL;
use schema RESTAURANT;

SELECT
util_db.public.se_grader(
step,
(actual = expected),
actual,
expected,
description
) AS graded_results
FROM
(
SELECT
'SEDW14' AS step,
(
SELECT
COUNT(*)
FROM
SUMMARIZEAGG_EXPERIENCE
) AS actual,
9 AS expected,
'SUMMARIZEAGG successfully applied to AISQL Restaurant' AS description
);
```

### Validate `AIAGG_STRENGTHS` Table

```sql
use database AISQL_HOL;
use schema RESTAURANT;

SELECT
util_db.public.se_grader(
step,
(actual = expected),
actual,
expected,
description
) AS graded_results
FROM
(
SELECT
'SEDW15' AS step,
(
SELECT
COUNT(*)
FROM
AIAGG_STRENGTHS
) AS actual,
3 AS expected,
'AIAGG_STRENGTHS successfully applied to AISQL Restaurant' AS description
);
```

If all validations return ✅, you have completed the AI SQL LAB\! 🎉
