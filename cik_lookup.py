# Built-in Python Modules
import urllib.parse
import urllib.request
import gzip
import io
import json

def extract_pre_sections(html):
    """
    Parses HTML to extract the content of all `<pre>` elements.
    
    The SEC page information in `<pre>` elements is extracted as follows:
        - pre_sections[0]: Header (column descriptions)
        - pre_sections[1]: Main table where each line is a CIK code, Company, and Name

    :param html: HTML object
    :return: List of strings corresponding to ``<pre>`` element(s)
    """

    pre_sections = []
    start_tag = "<pre>"
    end_tag = "</pre>"
    start = html.find(start_tag)

    # Locate and extract all <pre> elements
    while start != -1:
        end = html.find(end_tag, start)
        if end != -1:
            # Extract content between <pre> tags and strip extra whitepsace
            pre_content = html[start + len(start_tag):end].strip()
            pre_sections.append(pre_content)
            start = html.find(start_tag, end)
        else:
            break # No matching </pre> is found; error in HTML?
    
    return pre_sections


def main():
    search_url = "https://www.sec.gov/cgi-bin/cik_lookup"

    # User-Agent headers required by SEC guidelines
    headers = {
        "User-Agent": "Personal Use johnnyappleseed@gmail.com", # NOTE: Replace with your email (johnnyappleseed does work for testing purposes)
        "Accept-Encoding": "gzip, deflate",                     # Enables compressed responses
        "Host": "www.sec.gov"                                   # Required host header
    }

    # SEC search entries: company names to query
    # max request rate: 10 requests/second
    search_entries = {
        "Pulse",
        "Comcast",
        "Google",
        "ABC",
        "Apple",        # FIXME: Handle truncation if results are limited (e.g., refine queries?)
    }

    # Iterate over company names and make requests
    for entry in search_entries:
        # Valid URL format:
        # https://www.sec.gov/cgi-bin/cik_lookup?company={COMPANY_NAME}
        search_query = {"company": entry}
        encoded_query = urllib.parse.urlencode(search_query)
        full_url = f"{search_url}?{encoded_query}"

        # Create a request with required headers
        request = urllib.request.Request(full_url, headers=headers)

        try:
            # Open the request and read the response
            with urllib.request.urlopen(request) as response:
                # Check if response is compressed (gzip) and handle accordingly
                if response.info().get("Content-Encoding") == "gzip":
                    # Decompress gzip response
                    buffer = gzip.GzipFile(fileobj=io.BytesIO(response.read()))
                    html_content = buffer.read().decode("utf-8")
                else:
                    html_content = response.read().decode("utf-8")

            # Extract content from all <pre> elements
            pre_sections = extract_pre_sections(html=html_content)

            # Process the second <pre> section, which contains the table data
            if len(pre_sections) > 1:
                pre_table = pre_sections[1]
                data = {}

                # Parse each line of the table and extract CIK and company name
                for line in pre_table.split("\n"):
                    if '<a href="' in line:
                        # CIK = text within <a> tag
                        start_link = line.find('">') + 2
                        end_link = line.find("</a>")
                        cik = line[start_link:end_link].strip()

                        # Company name = text after </a> tag
                        company_start = line[end_link + 4:].strip()
                        data[cik] = company_start
                
                # Display results
                print(f"\nResults for '{entry}':")
                for cik, company in data.items():
                    print(f"{cik:<10}: {company}")

                # Write data to JSON
                # output_file = f"{entry.replace(' ', '_').lower()}_results.json"  # File name based on search entry
                # with open(output_file, "w", encoding="utf-8") as file:
                #     json.dump(data, file, indent=4)
                # print(f"Data saved to {output_file}")

            else:
                print(f"Error: Missing expected table for '{entry}'.")

        except urllib.error.HTTPError as e:
            print(f"HTTP Error for '{entry}': {e.code} {e.reason}")
        except urllib.error.URLError as e:
            print(f"URL Error for '{entry}': {e.reason}")
        except Exception as e:
            print(f"Unexpected error for '{entry}': {str(e)}")

if __name__ == "__main__":
    main()