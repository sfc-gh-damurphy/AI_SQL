import streamlit as st
import pandas as pd
from snowbook.executor import sql_executor

if "patched" not in st.session_state:
    old_sql_statement = sql_executor.run_single_sql_statement
    
    def patched_run_single_sql_statement(*args, **kwargs):
        result = old_sql_statement(*args, **kwargs)
        
        result_df = result.query_scan_data_frame
        select = []
        image_columns = {}
        import streamlit as st
        
        for col, type in result_df.dtypes:
            if type == "file":
                select.append(f"FL_GET_PRESIGNED_URL(CONCAT(FL_GET_STAGE({col}), '/', FL_GET_RELATIVE_PATH({col})), 604800) as {col}")
                image_columns[col] = st.column_config.ImageColumn()
            else:
                select.append(col)
        if image_columns:
            
            st.dataframe(result_df.select_expr(", ".join(select)), column_config=image_columns)
        else:
            return result
    
    sql_executor.run_single_sql_statement = patched_run_single_sql_statement
    st.session_state.patched = True
