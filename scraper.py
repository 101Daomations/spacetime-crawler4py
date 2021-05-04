import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import urllib.parse

# Question 1 - How many unique webpages
uniqueUrl = set()

# Question 2 - What is the longest page
# longestPage = [url, len]
longestPage = ["", 0]

# Question 3 - 50 most common words
mostCommon = {}

# Question 4 - How many subdomains in ics.uci.edu
subDomain = {}

# dictionary to keep track of tokens for simihash
tokenHash = {}

# Most common stop words
stopWords = {"a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any",
             "are", "aren't", "as", "at", " be", "because", "been", "before", "being", "below",
             "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't",
             "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from",
             "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd",
             "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
             "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
             "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not",
             "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
             "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
             "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
             "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
             "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
             "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while",
             "who", "who's",
             "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
             "your",
             "yours", "yourself", "yourselves",
             "for", "use", "our", "meet", "can", "also", "be", "na", "using", "will", "many", "based", "new", "title",
             "show", "may", "says", "reply", "read"}


# finds the next links to be scraped
def scraper(url, resp):
    # get next links
    links = extract_next_links(url, resp)
    # update the answer document with info from the current url being scraped
    createAnswerDoc()
    return links


def extract_next_links(url, resp):
    try:
        # set of links found
        # used set to avoid dupliates
        linksFound = set()

        # check if url is valid
        if is_valid(url):

            # Get a dictionary of all the tokens in the current url
            # Only returns a dictionary if the url has more than 200 tokens (excluding stopwords)
            # returns False otherwise
            tokens = goodText(url)

            #if the url has a good amount of text, hence type(tokens) == dict
            if type(tokens) == dict:

                # add it to dictionary for simihashing
                tokenHash[url] = tokens

                # check similarity
                similar = simihash(url, tokens)

                # check if link can be crawled, and not more than 90% similar with previous urls found
                if checkCrawl(resp) and (not similar):
                    # answer questions 1-4
                    answerQuestions(url, tokens)

                    # scrape the url for atags (links)
                    soup = BeautifulSoup(requests.get(url).content, "html.parser")
                    for link in soup.findAll("a"):
                        href = link.get("href")

                        # defragment href
                        href = urllib.parse.urljoin(url, href, allow_fragments=False)
                        href = defragment(href)

                        # check if link found is valid before adding it
                        if is_valid(href):
                            linksFound.add(href)

                    return list(linksFound)

        return []

    except:
        return []


# Check to see if url is valid
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
                + r"|calendar|events|event|py|mpg|odc|ppsx|pps|ff|ps|Z|z|r)$", parsed.path.lower()):
            return False

        # checks to see if url is a trap
        if trap(url):
            return False

        # Check to see if its has the right domain
        if not isValidDomain(url):
            return False

        # Check to see if url has been visited before
        if not isUnique(url):
            return False

        # filter out social media share links and page ids
        if social(url):
            return False

        return True
    except TypeError:
        print("TypeError for ", parsed)
        raise


# ---------------------------------Helper Functions---------------------------------

# checks if the url is of the right domain
def isValidDomain(url):
    # removed today.uci.edu/...
    domains = ["ics.uci.edu",
               "cs.uci.edu",
               "informatics.uci.edu",
               "stat.uci.edu"]

    # empty url
    if not url:
        return False

    # check for urls such as physICS.uci, economICS.uci... but include informatics
    if not isICS(url):
        return False

    # loop through domains given
    for d in domains:
        if d in url:
            return True
    return False


# checks to see if its a trap
def trap(url):
    # trap urls that we've ran into
    trapURL = ["~eppstein/junkyard", "mt-live", "/event", "/events", "ics.uci.edu/ugrad/honors/",
               "www.ics.uci.edu/honors", "evoke.ics.uci.edu/qs-personal-data-landscapes-poster",
               "archive.ics.uci.edu", "flamingo.ics.uci.edu/localsearch/fuzzysearch", "/pdf", "grape.ics.uci.edu",
               "zImage_paapi"]

    # repeating directories
    #got this regex from https://support.archive-it.org/hc/en-us/articles/208332963-Modify-your-crawl-scope-with-a-Regular-Expression
    if re.match("^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$", url):
        return True

    # regex wasnt catching everything so made a function as well
    if repeatingDirect(url):
        return True

    # check to see if url is apart of a blacklisted url
    for t in trapURL:
        if t in url:
            return True

    # Check to see if url is too long
    if len(url) > 150:
        return True


# repeating directs
def repeatingDirect(url):
    #get just the path of the url
    parse = urlparse(url)
    path = parse.path

    #Split the path by "/" into a list
    pathList = path.split("/")

    #Remove empty strings from the list
    #gotten from paths such as /hello//directory/
    for i in pathList.copy():
        if i == "":
            pathList.remove("")

    #Removed numbers from the list
    #accounts for dates such as /2020/04/04
    for i in pathList.copy():
        if not i.isalpha():
            pathList.remove(i)

    #loop through the paths
    for direct in pathList:
        #if a path shows up more than once, its repeating, hence a trap
        if (pathList).count(direct) > 1:
            return True

    #returns false otherwise
    return False


# removes the fragment from a url if it has it
def defragment(url):
    #checks to see if a fragment exists
    if "#" in url:
        #get the starting index of the fragment
        index = url.find("#")
        #return the string all the way up to the fragment
        return url[:index]
    #return the url if theres no fragment
    return url


# checks to see if the link is for sharing to a social media or page id
def social(url):
    if "?" in url:
        return True
    return False


# checks to see if url has been visted before
def isUnique(url):
    if url in uniqueUrl:
        return False
    return True


# check if link can be crawled
def checkCrawl(resp):
    #check to see if the response status is good and the url has text in it
    if (resp.status >= 200 and resp.status <= 299) and resp.raw_response:
        return True
    return False


# check to see if the page has good amount of text
def goodText(url):
    #tokenizes the url
    tokens = tokenize(url)

    #counts up the total amount of all the tokens excluding stop words
    count = sum(list(tokens.values()))

    #returns a dictionary of tokens if url has good amount of text, false otherwise
    #this is done to make the program more efficient as we would only have to tokenize once
    #in goodtext() rather than twice in both goodtext() and answerquestions() called in extract_next_links()
    if count > 200:
        return tokens
    return False


# scrape the webpage and tokenize
def tokenize(url):
    # dict to keep track of tokens
    tokens = {}

    # scrape the url to get tokens
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    text = soup.get_text(separator=' ', strip=True)

    # remove all non alphanumeric characters
    text = re.sub('[^A-Za-z]+', ' ', text)

    # lowercase all characters
    text = text.lower()

    # split string into a list
    tokenList = text.split()

    # remove stop words and add it token dict
    for token in tokenList:
        if token not in stopWords and len(token) >= 2:
            if token not in tokens:
                tokens[token] = 1
            else:
                tokens[token] += 1

    return tokens


# Detect non-ics, "physICS, economICS... but include informatics"
# used in functions where we want to detect validity
def isICS(url):
    if "informatics.uci.edu" in url:
        return True

    #make sure its not a non-ics like physICS, economICS,...
    if isICS2(url):
        return True
    return False


# Detect non-ics, "physICS, economICS..."
#used in functions where we want to check for just "ics.uci.edu"
#link in answerQuestions(), question 4
def isICS2(url):
    #if ics.uci.edu in url, check if theres a character before the i in ics
    if "ics.uci.edu" in url:
        #get the index for "ics.uci.edu"
        index = url.find("ics.uci.edu")
        #check if the char before the i in ics is an alpha
        #example: phy"s"ics.uci.edu vs www"."ics.uci.edu
        if (url[index - 1]).isalpha():
            return False
    return True


# Extra credit, simihashing
def simihash(url, tokens):
    # only want to check similarity of the url if the url hasnt been visited before
    if url not in tokenHash:
        # create a token set for current url
        tokenSetA = set(tokens.keys())

        # loop through the tokens from urls already found and get their token set
        for urls in tokenHash:
            tokenSetB = set(urls.keys())

            # get the intersection of the two sets and compare length to determine similarity
            intersection = tokenSetA.intersection(tokenSetB)

            # Compare lengths, what percentage of the tokens in the url is the same as another
            # url already seen
            lenA = len(tokenSetA)
            lenIntersection = len(intersection)

            # make sure the intersection is greater than 0 to prevent 0 division
            if lenIntersection > 0:
                similarity = lenIntersection / lenA

                # if url found is more than 90% similar than we dont want it
                if similarity > 0.90:
                    return True

    return False


# ------------------- Functions related to answering 1-4--------------------------

# update the global variables to answer questions 1-4
def answerQuestions(url, tokens):
    global uniqueUrl
    global longestPage
    global mostCommon
    global subDomain

    # Question 1 - unique urls
    # get rid of the fragment in the url
    defragmentURL = defragment(url)
    uniqueUrl.add(defragmentURL)

    # Question 2 - Longest url
    count = sum(list(tokens.values()))
    if count > longestPage[1]:
        longestPage = [defragmentURL, count]

    # Question 3 - Top 50 tokens
    for token in tokens:
        if token in mostCommon:
            mostCommon[token] += tokens[token]
        else:
            mostCommon[token] = tokens[token]

    # Queston 4 - Count ics.uci.edu subdomains
    # get parsed url object to get subdomain
    parsed = urlparse(defragmentURL)

    if ("ics.uci.edu" in parsed.hostname) and (isICS2(url)):
        if parsed.hostname in subDomain:
            subDomain[parsed.hostname] += 1
        else:
            subDomain[parsed.hostname] = 1


# write answers for the 4 questions into a text file
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
        for word, freq in sorted(mostCommon.items(), key=lambda x: -x[1])[:50]:
            file.write(f"<{word}> - <{freq}>\n")
        file.write("\n")
        file.write(f"Subdomains: \n")
        for subdomain, freq in sorted(subDomain.items(), key=lambda x: x[0]):
            file.write(f"http://{subdomain}, {freq}\n")
        file.write(f"===============================")
        file.close()
    except:
        pass
