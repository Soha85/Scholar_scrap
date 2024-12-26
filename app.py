import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st
st.set_page_config(layout="wide")

def generate_bibtex_from_scraped_data(title, authors, publication_details):
    """
    Generate a basic BibTeX entry from scraped research details.
    :param title: Title of the research paper.
    :param authors: List of authors (comma-separated string or list).
    :param publication_details: Publication details (conference, journal, year).
    :return: A formatted BibTeX entry as a string.
    """
    # Generate a unique key for the BibTeX entry
    if authors:
        first_author = authors.split(",")[0].strip().replace(" ", "_")
    else:
        first_author = "Unknown_Author"
    bibtex_key = f"{first_author}_{title[:20].replace(' ', '_').replace(':', '').replace(',', '')}"

    # Extract the year from publication details
    year = "Unknown Year"
    for word in publication_details.split():
        if word.isdigit() and len(word) == 4:  # Assume a 4-digit year
            year = word
            break

    # Construct the BibTeX entry
    bibtex_entry = f"""@article{{{bibtex_key},
      title = {{{title}}},
      author = {{{authors}}},
      year = {{{year}}},
      journal = {{{publication_details}}}
    }}"""
    return bibtex_entry
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

     # Extract the user's title
    user_title = soup.find("div", class_="gsc_prf_il")
    user_title = user_title.text if user_title else "Unknown Title"
    
   # Extract research titles
    titles,citations,bibtex_entries = [],[],[]
    for row in soup.find_all("tr", class_="gsc_a_tr"):
        title_cell = row.find("td", class_="gsc_a_t")
        if title_cell:
            title = title_cell.find("a").text  # The title text is inside the <a> tag
            titles.append(title)
       # Extract all citation details
        citation_cells = title_cell.find_all("div", class_="gs_gray")
        if citation_cells:
            # Combine text from all <div> elements, including <span>
            citation = " | ".join([cell.get_text(strip=True) for cell in citation_cells])
            citations.append(citation)
           # Extract BibTeX details
            citation_cells = title_cell.find_all("div", class_="gs_gray")
            if citation_cells:
                authors = citation_cells[0].get_text(strip=True) if len(citation_cells) > 0 else "Unknown Authors"
                publication_details = citation_cells[1].get_text(strip=True) if len(citation_cells) > 1 else "Unknown Publication Details"
                citations.append(f"{authors} | {publication_details}")

                # Generate BibTeX from scraped data
                bibtex_entry = generate_bibtex_from_scraped_data(title, authors, publication_details)
                bibtex_entries.append(bibtex_entry)
    return {"name": user_name,"title":user_title, "researches": titles,"citations":citations,"Bibtex":bibtex_entries}

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
                        "User Title":details["title"],
                        "Research Titles": "\n".join(details["researches"]),
                        "Citations":"\n".join(details["citations"]),
                        "BibTex":"\n".join(details["Bibtex"])
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
