import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st
st.set_page_config(layout="wide")


# Function to scrape user name and research titles from Google Scholar
def scrape_scholar_details(scholar_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(scholar_url, headers=headers)
    if response.status_code != 200:
        return {"name": "N/A", "titles": ["Failed to retrieve data"]}

    soup = BeautifulSoup(response.content, "html.parser")

    # Extract the user's name
    user_name = soup.find("div", id="gsc_prf_in")
    user_name = user_name.text if user_name else "Unknown User"

   # Extract research titles
    titles,citations = [],[]
    for row in soup.find_all("tr", class_="gsc_a_tr"):
        title_cell = row.find("td", class_="gsc_a_t")
        if title_cell:
            title = title_cell.find("a").text  # The title text is inside the <a> tag
            titles.append(title)
        citation_cell = row.find("td",class_="gsc_a_c")
        if citation_cell:
            citation = citation_cell.find("a").text
            citations.append(citation)
    
    return {"name": user_name, "titles": titles,"citations":citations}

# Streamlit app to process the file
def main():
    st.title("Google Scholar Research Title Scraper")

    # Upload Excel file
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
    if uploaded_file:
        # Load Excel file into DataFrame
        df = pd.read_excel(uploaded_file)

        # Display the DataFrame
        st.write("Uploaded DataFrame:")
        st.dataframe(df)

        # Select column containing Google Scholar links
        column_name = st.selectbox("Select the column with Google Scholar links:", df.columns)

        if st.button("Scrape Research Titles"):
            # Create a results list
            results = []

            # Iterate over each Google Scholar link
            for index, row in df.iterrows():
                scholar_url = row[column_name]
                #st.write(f"Scraping: {scholar_url}")
                try:
                    details = scrape_scholar_details(scholar_url)
                    results.append({
                        "User Name": details["name"],
                        "Research Titles": "\n".join(details["titles"]),
                        "Citations":"\n".join(details["citations"])
                    })
                except Exception as e:
                    results.append({
                        "User Name": "Error",
                        "Research Titles": str(e)
                    })

            # Convert results to DataFrame
            result_df = pd.DataFrame(results)

            # Display results
            st.write("Scraped Results:")
            st.dataframe(result_df)

            # Download the results as an Excel file
            result_file = "scraped_results.xlsx"
            result_df.to_excel(result_file, index=False)
            with open(result_file, "rb") as file:
                st.download_button(
                    label="Download Results",
                    data=file,
                    file_name="scraped_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


if __name__ == "__main__":
    main()
