import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import urllib.parse


#Question 1 - How many unique webpages
uniqueUrl = set()

#Question 2 - What is the longest page
#longestPage = [url, len]
longestPage = ["", 0]

#Question 3 - 50 most common words
mostCommon = {}

#Question 4 - How many subdomains in ics.uci.edu
subDomain = {}


#Most common stop words
stopWords = {"a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any",
             "are", "aren't", "as", "at", " be", "because", "been", "before", "being", "below",
             "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't",
             "do", "does", "doesn't","doing","don't", "down", "during", "each", "few", "for", "from",
             "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd",
             "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
             "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
             "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not",
             "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
             "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
             "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
             "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
             "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
             "we've","were","weren't","what","what's","when","when's","where","where's","which","while","who","who's",
             "whom","why","why's","with", "won't","would","wouldn't","you","you'd","you'll","you're","you've","your",
             "yours","yourself", "yourselves"}



def scraper(url, resp):
    links = extract_next_links(url, resp)
    returned = [link for link in links if is_valid(link)]
    createAnswerDoc()
    return returned


def extract_next_links(url, resp):
    #set of links found
    linksFound = set()

    #check if link can be crawled
    if checkCrawl(resp) and is_valid(url):
        #answer questions 1-4
        answerQuestions(url)

        #scrape the url for atags (links)
        soup = BeautifulSoup(requests.get(url).content, "html.parser")
        for link in soup.findAll("a"):
            href = link.get("href")

            #defragment href
            href = urllib.parse.urljoin(url, href, allow_fragments=False)
            #check if link is valid
            if is_valid(href):
                linksFound.add(href)

        return list(linksFound)

    return []


def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False

        # Check to see if the url does not point to a webpage
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|txt|jpg|img"
            + r"|calendar|events|event|py|)$", parsed.path.lower()):
            return False

        # Check to see if its has the right domain
        if not isValidDomain(url):
            return False

        #Check to see if url is too long
        if len(url) > 325:
            return False

        #Check to see if url has been visited before
        if not isUnique(url):
            return False

        #Check to see if url has a good amount of content
        if not goodText(url):
            return False


        return True
    except TypeError:
            print ("TypeError for ", parsed)
            raise



#---------------------------------Helper Functions---------------------------------

#checks if the url is of the right domain
def isValidDomain(url):
    domains = ["ics.uci.edu",
               "cs.uci.edu",
               "informatics.uci.edu",
               "stat.uci.edu",
               "today.uci.edu/department/information_computer_sciences"]

    if not url:
        return False
    #loop through domains given

    for d in domains:
        if d in url:
            return True
    return False


#removes the fragment from a url if it has it
def defragment(url):
    if "#" in url:
        index = url.find("#")
        return url[:index]
    return url


#checks to see if url has been visted before
def isUnique(url):
    if url in uniqueUrl:
        return False
    return True


#check if link can be crawled
def checkCrawl(resp):
    if (resp.status >= 200 and resp.status <= 299) and resp.raw_response:
        return True
    return False


#check to see if the page has good amount of text
def goodText(url):
    tokens = tokenize(url)
    count = sum(list(tokens.values()))

    #https://whiteboard-mktg.com/how-much-content-is-good-for-seo-rankings/
    #based on forbes any website with less than 300 words per page is considered "thin"
    if count > 300:
        return True
    return False


#scrape the webpage and tokenize
def tokenize(url):
    #dict to keep track of tokens
    tokens = {}

    #scrape the url to get tokens
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    text = soup.get_text(separator=' ', strip=True)

    #remove all non alphanumeric characters
    text = re.sub('[^A-Za-z0-9]+', ' ', text)

    #lowercase all characters
    text = text.lower()

    #split string into a list
    tokenList = text.split()

    #remove stop words and add it token dict
    for token in tokenList:
        if token not in stopWords and len(token) >= 2:
            if token not in tokens:
                tokens[token] = 1
            else:
                tokens[token] += 1

    return tokens


#update the global variables to answer questions 1-4
def answerQuestions(url):
    global uniqueUrl
    global longestPage
    global mostCommon
    global subDomain

    #Question 1 - unique urls
    #get rid of the fragment in the url
    defragmentURL = defragment(url)
    uniqueUrl.add(defragmentURL)


    #Question 2 - Longest url
    tokens = tokenize(url)
    count = sum(list(tokens.values()))
    if count > longestPage[1]:
        longestPage = [defragmentURL, count]


    #Question 3 - Top 50 tokens
    for token in tokens:
        if token in mostCommon:
            mostCommon[token] += tokens[token]
        else:
            mostCommon[token] = tokens[token]

    #Queston 4 - Count ics.uci.edu subdomains
    if "ics.uci.edu" in url:
        if defragmentURL in subDomain:
            subDomain[defragmentURL] += 1
        else:
            subDomain[defragmentURL] = 1


#write answers for the 4 questions into a text file
def createAnswerDoc():
    global uniqueUrl
    global longestPage
    global mostCommon
    global subDomain

    try:
        file = open("answer.txt", "w")
        file.write(f"===============================\n")
        file.write(f"Number of Unique URLs: {len(uniqueUrl)}\n\n")
        file.write(f"Longest Page & Number of Words: {longestPage[0]} , {longestPage[1]} \n\n")

        file.write(f"Most Common Words: \n")
        for word, freq in sorted(mostCommon.items(), key=lambda x:-x[1])[:50]:
            file.write(f"<{word}> - <{freq}>\n")
        file.write("\n")
        file.write(f"Subdomains: \n")
        for subdomain, freq in sorted(subDomain.items(),key=lambda x:x[0]):
            file.write(f"{subdomain}, {freq}\n")
        file.write(f"===============================")
        file.close()
    except:
        pass
