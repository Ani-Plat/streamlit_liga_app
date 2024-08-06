import os
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine
import seaborn as sns
from datetime import datetime, timedelta

howWarningOnDirectExecution = False
st.set_page_config(layout="wide")

os.environ['USER'] = 'default'
os.environ['HOST'] = '46.162.205.10'
os.environ['PORT'] = '9000'
os.environ['DATABASE'] = 'default'
os.environ['PASSWORD'] = '5Ir4Bnez0ca9'


USER = os.getenv('USER')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
DATABASE = os.getenv('DATABASE')
PASSWORD = os.getenv('PASSWORD')

print(HOST, PORT, DATABASE, USER)

if HOST is None or PORT is None or DATABASE is None:
    print("One or more environment variables (HOST, PORT, DATABASE) are not set.")
else:
    # Use the host, port, and database in your code
    eng = create_engine(f'clickhouse+native://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}')
    print("Engine created successfully:", eng)


def exec_query(query: str, con=eng):
    return pd.read_sql_query(query, con=con)


# Streamlit Sidebar for Section Selection
section = st.sidebar.selectbox(
    'Choose a Section',
    ('Dashboard Home', "Logs Performance Analysis", "Performance Analysis")
)

# Page Title
st.title("Data Analysis Dashboard")

# Colors and Theme
sns.set_theme(style="whitegrid")
PALETTE = "viridis"

if section == 'Dashboard Home':
    st.write("""
    ## Welcome to the Data Analysis Dashboard. 
    Use the sidebar to navigate to different sections.
    """)

elif section == "Logs Performance Analysis":

    cols1, cols2 = st.columns((1, 2))
    format = 'MMM DD, YYYY'


    min_date = datetime.utcfromtimestamp(
        exec_query("select MIN(dateTime) from successlogs").values[0][0].astype('O') / 1e9).date()
    max_date = datetime.utcfromtimestamp(
        exec_query("select MAX(dateTime) from successlogs").values[0][0].astype('O') / 1e9).date()

    start_date = cols1.date_input('Start date', min_date)
    end_date = cols1.date_input('End date', max_date)

    if start_date > end_date:
        st.error('Error: End date must fall after start date.')


    # start_date, end_date = slider

    # slider = cols1.slider('Select date', min_value=max_days, value=start_date, max_value=end_date, format=format)

    diff_score_query = f"""
    SELECT
    policyHolderId,
    plateNumber,
    MIN(score) AS MinScore,
    MAX(score) AS MaxScore,
    MIN(bmClass) AS MinBmClass,
    MAX(bmClass) AS MaxBmClass,
    CASE WHEN COUNT(DISTINCT Mark) > 1 THEN 'Yes' ELSE 'No' END AS Mark,
    CASE WHEN COUNT(DISTINCT Model) > 1 THEN 'Yes' ELSE 'No' END AS Model,
    CASE WHEN COUNT(DISTINCT Region) > 1 THEN 'Yes' ELSE 'No' END AS Region,
    CASE WHEN COUNT(DISTINCT Town) > 1 THEN 'Yes' ELSE 'No' END AS Town,
    MAX(score) - MIN(score) AS ScoreDifference
FROM successlogs
WHERE dateTime between '{start_date}' and '{end_date}'
GROUP BY policyHolderId, plateNumber 
"""

    error_query = f"""select error, count(error) as count from errorlogs
                    WHERE dateTime between '{start_date}' and '{end_date}'
                    group by error
                    order by count desc """

    col1, col2 = st.columns(2)

    with col1:
        st.write(exec_query(error_query))


        col3, col4 = st.columns(2)
        error_count = f"SELECT COUNT(*) FROM errorlogs WHERE dateTime between '{start_date}' and '{end_date}';"
        success_count = f"SELECT COUNT(*) FROM successlogs WHERE dateTime between '{start_date}' and '{end_date}';"
        with col3:
            st.metric(label="Success", value=exec_query(success_count).values, delta_color="inverse")
        with col4:
            st.metric(label="Error", value=exec_query(error_count).values, delta_color="inverse")

    # with col2:
    #     # Fetch unique plate numbers from the database
    #     unique_numbers_query = f"SELECT DISTINCT plateNumber FROM successlogs WHERE dateTime between '{start_date}' and '{end_date}' order by plateNumber"
    #     unique_numbers_result = exec_query(unique_numbers_query)
    #     unique_numbers = ['ALL'] + list(unique_numbers_result["plateNumber"].unique())
    #
    #     selected_number = st.selectbox("Select a Plate Number to filter:", unique_numbers, key="plate_number_selectbox")

    #     if 'selected_number' not in st.session_state:
    #         st.session_state.selected_number = "ALL"
    #
    #     st.session_state.selected_number = selected_number
    #
    #     # Apply filter based on selected plate number
    #     if selected_number == "ALL":
    #         st.write(exec_query(diff_score_query))  # Show all data
    #     else:
    #         # Query with the selected plate number filter
    #         query_with_filter = f"""
    #             SELECT
    #                 policyHolderId,
    #                 plateNumber,
    #                 MIN(score) AS MinScore,
    #                 MAX(score) AS MaxScore,
    #                 MIN(bmClass) AS MinBmClass,
    #                 MAX(bmClass) AS MaxBmClass,
    #                 CASE WHEN COUNT(DISTINCT Mark) > 1 THEN 'Yes' ELSE 'No' END AS Mark,
    #                 CASE WHEN COUNT(DISTINCT Model) > 1 THEN 'Yes' ELSE 'No' END AS Model,
    #                 CASE WHEN COUNT(DISTINCT Region) > 1 THEN 'Yes' ELSE 'No' END AS Region,
    #                 CASE WHEN COUNT(DISTINCT Town) > 1 THEN 'Yes' ELSE 'No' END AS Town,
    #                 MAX(score) - MIN(score) AS ScoreDifference
    #             FROM successlogs
    #             WHERE plateNumber = '{selected_number}' and dateTime between '{start_date}' and '{end_date}'
    #             GROUP BY policyHolderId, plateNumber limit 20
    #         """
    #         st.write(exec_query(query_with_filter))  # Show filtered data
    #
    #
    #     def get_data_to_download():
    #         if selected_number == "ALL":
    #             return exec_query(diff_score_query).to_csv().encode('utf-8')
    #         else:
    #             return exec_query(query_with_filter).to_csv().encode('utf-8')
    #
    #
    #     csv_data = get_data_to_download()
    #     st.download_button("Download CSV", csv_data, "file.csv", "text/csv", key='download-csv')


    col1, col2 = st.columns(2)
    with col1:
        try:
            plt.pie([exec_query(error_count).values[0][0], exec_query(success_count).values[0][0]], autopct='%1.0f%%',
                    startangle=90, colors=['#FBB766', '#6B7A97'])
            st.pyplot(plt)
        except:
            st.subheader("Please Select Another Range, there is not enough data")


##### Performance

# elif section == "Performance Analysis":
#
#     data = exec_query("select * from contract")
#
#     min_date = pd.to_datetime(exec_query("select MIN(ContractCreationDate) from contract").values[0][0]).date()
#     max_date = pd.to_datetime(exec_query("select MAX(ContractCreationDate) from contract").values[0][0]).date()
#
#     min_date1 = pd.to_datetime(exec_query("select MIN(ContractStartDate) from contract").values[0][0]).date()
#     max_date1 = pd.to_datetime(exec_query("select MAX(ContractStartDate) from contract").values[0][0]).date()
#
#     min_date2 = pd.to_datetime(exec_query("select MIN(ContractEndDate) from contract").values[0][0]).date()
#     max_date2 = pd.to_datetime(exec_query("select MAX(ContractEndDate) from contract").values[0][0]).date()
#
#     col1, col2, col3, col4, col5 = st.columns(5)
#
#     # Streamlit double-ended slider
#     with col1:
#         selected_range_creation = st.slider(
#             'Contract creation date',
#             min_value=min_date,
#             max_value=max_date,
#             value=(min_date, max_date)
#         )
#     with col3:
#         selected_range_start = st.slider(
#             'Contract start date',
#             min_value=min_date1,
#             max_value=max_date1,
#             value=(min_date1, max_date1)
#         )
#     with col5:
#         selected_range_end = st.slider(
#             'Contract end date',
#             min_value=min_date2,
#             max_value=max_date2,
#             value=(min_date2, max_date2)
#         )

    # data = exec_query("SELECT * FROM claim LEFT JOIN contract ON claim.policy_holder_id = contract.PolicyHolderId;")

    # col1, col2 = st.columns(2)
    # with col1:
    #     print("h")
    # plt.figure(figsize=(14, 7))
    # x = pd.DataFrame(data.groupby("scores").sum("accident_number")["accident_number"]/data.groupby("scores").sum("contract_days_passed_duration")["contract_days_passed_duration"])
    # plt.plot(x)
    # plt.scatter(y=x, x=x.index)
    # plt.title('Accident Frequency Score No Filter', fontsize = 30)
    # plt.xlabel('Scores')
    # st.pyplot(plt)
    # with col2:
    #     print("H")
    # plt.figure(figsize=(14, 7))
    # x = pd.DataFrame(data.groupby("score_with_hardfilter").sum("accident_number")["accident_number"]/data.groupby("score_with_hardfilter").sum("contract_days_passed_duration")["contract_days_passed_duration"])
    # plt.plot(x)
    # plt.scatter(y=x, x=x.index)
    # plt.title('Accident Frequency Scores', fontsize =30)
    # plt.xlabel('Scores')
    # st.pyplot(plt)
    #
    # col1, col2 = st.columns(2)
    # with col1:
    #     plt.figure(figsize=(14, 7))
    #     x = pd.DataFrame(data.groupby("BMClass").sum("accident_number")["accident_number"]/data.groupby("BMClass").sum("contract_days_passed_duration")["contract_days_passed_duration"])
    #     plt.plot(x)
    #     plt.scatter(y=x, x=x.index)
    #     plt.title('Accident Frequency bmClass', fontsize =30)
    #     plt.xlabel('Scores')
    #     st.pyplot(plt)
    # with col2:
    #     plt.figure(figsize=(14, 7))
    #     data.groupby("scores").mean()["bmClass"].plot(kind="bar")
    #     plt.title('Mean BmClass for Each Score', fontsize =30)
    #     st.pyplot(plt)
    #
    #
    # col1, col2 = st.columns(2)
    # with col1:
    #     selected_number1 = st.selectbox("Select bmClass to filter:", np.sort(data.bmClass.unique()), key = 'box1')
    #     plt.figure(figsize = (14,7))
    #     data[data['bmClass'] == selected_number1]['scores'].value_counts().sort_index().plot(kind='bar')
    #     plt.title("Distribution of Scores For bmClass", fontsize =30)
    #     st.pyplot(plt)
    # with col2:
    #     selected_number2 = st.selectbox("Select bmClass to filter:", np.sort(data.bmClass.unique()), index=24 ,key = 'box2')
    #     plt.figure(figsize=(14, 7))
    #     data[data['bmClass'] == selected_number2]['scores'].value_counts().sort_index().plot(kind='bar')
    #     plt.title("Distribution of Scores For bmClass", fontsize =30)
    #     st.pyplot(plt)
    #
