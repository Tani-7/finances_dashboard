import streamlit as st
import pandas as pd
# import plotly.express as px
import json
import os


st.set_page_config(page_title='Mpesa Finances Tracker',
                   page_icon='$$', layout='wide')

categories_file = 'categories.json'

if 'categories' not in st.session_state:
    st.session_state.categories = {'Uncategorized': [], }

if os.path.exists(categories_file):
    with open(categories_file, 'r') as f:
        st.session_state.categories = json.load(f)


def save_categories():
    with open(categories_file, 'w') as f:
        json.dump(st.session_state.categories, f)


def categorize_transactions(df):
    df['Category'] = 'Uncategorized'

    for category, keywords in st.session_state.categories.items():
        if category == 'Uncategorized' or not keywords:
            continue

        lower_case = [keyword.lower().strip() for keyword in keywords]

        for idx, row in df.iterrows():
            details = row['Details'].lower().strip()
            if details in lower_case:
                df.at[idx, 'Category'] = category
    return df


def load_transactions(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]
        df['Amount'] = df['Amount'].str.replace(',', '').astype(float)
        df['Date'] = pd.to_datetime(df['Date'], format='%d %b %Y')

        return categorize_transactions(df)

    except Exception as e:
        st.error(f'Error Processing Your Data: {str(e)}')
        return None


def kw_to_cat(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories
        return True

    return False


def main():
    st.title("Charlie's Finance Dasbhoard")

    file_import = st.file_uploader(
        'Upload your recent transactions as CSV', type=['csv'])

    if file_import is not None:
        df = load_transactions(file_import)

        if df is not None:
            debits_df = df[df['Debit/Credit'] == 'Debit'].copy()
            credit_df = df[df['Debit/Credit'] == 'Credit'].copy()

            st.session_state.debits_df = debits_df.copy()

            tab1, tab2 = st.tabs(['Expenses(Debits)', 'Payments(Credits)'])
            with tab1:
                new_cat = st.text_input('New Category Name')
                add_button = st.button('Add Category')

                if add_button and new_cat:
                    if new_cat not in st.session_state.categories:
                        st.session_state.categories[new_cat] = []
                        save_categories()
                        st.rerun()

                st.subheader('Your Expenses')

                edited_df = st.data_editor(
                    st.session_state.debits_df[[
                        "Date", "Details", "Amount", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f AED"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )

                save_button = st.button('Apply Changes', type='primary')
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_cat = row['Category']
                        if new_cat == st.session_state.debits_df.at[idx, 'Category']:
                            continue

                        details = row['Details']
                        st.session_state.debits_df.at[idx,
                                                      'Category'] = new_cat
                        kw_to_cat(new_cat, details)
                st.subheader('Expenses Summary')
                cat_totals = st.session_state.debits_df.groupby(
                    'Category')['Amount'].sum().reset_index()
                cat_totals = cat_totals.sort_values('Amount', ascending=False)

                st.dataframe(
                    cat_totals,
                    column_config={'Amount': st.column_config.NumberColumn(
                        'Amount', format='%.2f KSh')},
                    use_container_width=True,
                    hide_index=True
                )

                # fig = px.pie(cat_totals, values='Amount',
                # names='Category', title='Expenses by Category')

                with tab2:
                    st.subheader('Payments Summary')
                    total_payments = credit_df['Amount'].sum()
                    st.metric('Total Payments', f'{total_payments:,.2f}')
                    st.write(credit_df)


main()
