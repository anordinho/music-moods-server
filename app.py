import os
import string
import time
import nltk
from flask import Flask, flash, request, redirect, jsonify
from werkzeug.utils import secure_filename
from langdetect import detect
from nltk import sent_tokenize
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def lyric_dataset_load(lyric_file_path):
    lyric_file = open(lyric_file_path, 'rt')
    lyric_file_content = lyric_file.read()
    lyric_file.close()

    # Using NLTK to Split the Music Lyrics to Indivual Words
    sentence_tokenized_lyrics = sent_tokenize(lyric_file_content)

    """print('**** Start Sentence Tokens *****') """
    print(sentence_tokenized_lyrics[:10])
    """print('**** End Sentence Tokens *****') """
    word_tokenized_lyrics = word_tokenize(lyric_file_content)
    # Converting all words in the lyrical content to Lowercase
    word_tokenized_lyrics = [w.lower() for w in word_tokenized_lyrics]
    # Removing all the Panctuation Marks from Words
    lyric_content_table = str.maketrans('', '', string.punctuation)
    lyric_punct_stripped = [w.translate(
        lyric_content_table) for w in word_tokenized_lyrics]
    # Removing Non-Alphabetic from the Lyrics Contents
    lyric_content_alpbtsOnly = [
        word for word in lyric_punct_stripped if word.isalpha()]
    lyric_stopwords = set(stopwords.words('english'))
    lyric_content_wo_stopwords = [
        w for w in lyric_content_alpbtsOnly if not w in lyric_stopwords]
    return lyric_content_wo_stopwords
    # clean_lyrical_content output


def detect_lyric_lang(lyrics_content):
    lyrics_language = detect(lyrics_content)
    return lyrics_language


def load_lang_corpus(detected_language):
    if detected_language.upper() in ['SW', 'EN']:
        try:
            abusive_words_list = []
            corpus_file = open(
                'corpus/'+detected_language.lower()+'.csv', 'rt')
            for word in corpus_file:
                abusive_words_list.append(word.lower().strip('\n'))
            return abusive_words_list
        except EnvironmentError:
            return False
        finally:
            corpus_file.close()
    else:
        return False


@app.route('/file', methods=['GET', 'POST'])
def upload_file():
    # if request.method == 'POST':
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # 2. Loading Lyrics Dataset and Spliting it with WhiteSpace
        clean_lyric = lyric_dataset_load(UPLOAD_FOLDER+"/"+filename)
        clean_lyric_str = str(clean_lyric)

        lyric_content_lang = detect_lyric_lang(clean_lyric_str)
        print('--------------------------------------------')
        print('Detected Lyrical Content Language : ' +
              lyric_content_lang.upper())
        print('--------------------------------------------')

        sorted_lyric_content = sorted(set(clean_lyric))

        """
            print('-------------------------------------------\nTotal Unique \
            Words found in the Lyrics\n-----------------------------------')
            print(len(set(sorted_lyric_content)))
            print('--------------------------------------\nList of Unique \
            Words found in the Lyrics\n-------------------------------')
            print(sorted_lyric_content)
            print('--------------------------------\nCalculating Frequency \
            Distribution of the Lyrics\n-------------------------')
            """

        freqDist_lyric_content = nltk.FreqDist(clean_lyric)

        # print(freqDist_lyric_content)
        print('-------------------------------------------\nCalculating Frequency of \
            Words of the Lyrics\n-------------------------------------------')
        lyric_list_print = freqDist_lyric_content.most_common(
            len(set(sorted_lyric_content)))
        print(*lyric_list_print, sep=" - ")
        print('--------------------------------------------------------\nChecking  \
            for Abusive Words in the Lyrics in ' +
              lyric_content_lang.upper()+' Language'+'\n----------------\
                       ----------------------------------------')
        try:
            abusive_words = load_lang_corpus(lyric_content_lang)
            abusive_words = set(abusive_words)

        except Exception as lmcrError:
            print('Lyrical Music Content Rating Algorithm \
            Encountered Error - '+str(lmcrError))

        abusive_wordsFound = clean_lyric_str.split('\n')
        for sentence in abusive_wordsFound:
            # line_number = str(abusive_wordsFound.index(sentence)+1)
            for key in ['.', ',', '"', "'", '?', '!', ':', ';', '\
            (', ')', '[', ']', '{', '}']:
                sentence = sentence.replace(key, '')
                abusiveWords = [eachWord for eachWord in sentence.lower(
                ).split() if eachWord in abusive_words]
                if abusiveWords == []:
                    continue
                else:
                    time.sleep(0.5)

        # Getting number of Words in the lyrics and number of abusive words
        total_words_in_lyrics = len(set(clean_lyric_str))
        total_abusiveWords_in_lyrics = len(abusiveWords)
        total_cleanWords_in_lyrics = (
            total_words_in_lyrics - total_abusiveWords_in_lyrics)

        print('LYRICAL MUSIC CONTENT RATING ALGORITHM ANALYSIS RESULTS')
        print('-------------------------------------------------------')
        print('** TOTAL WORDS IN THE LYRICS - '+str(total_words_in_lyrics))
        print('** TOTAL CLEAN WORDS IN LYRICS - ' +
              str(total_cleanWords_in_lyrics))
        print('\n*** TOTAL ABUSIVE WORDS IN LYRICS - ' +
              str(total_abusiveWords_in_lyrics))
        print('---------------------------------------------------------')
        print('Detailed Analysis: ')

        print('LMCR Found '+str(total_abusiveWords_in_lyrics) +
              ' Potentially Abusive Words in the Lyrics')
        x_words = ''
        for eachWord in abusiveWords:
            x_words += eachWord+', '

        print('Abusive Words Found are : \n'+x_words[:-2])
        print('------------------------------\n')
        results = [
            {
                'abusive_words': x_words[:-2],
                'Total_abusive': +
                total_abusiveWords_in_lyrics}
        ]
        return jsonify(results)
    # return '''
    #         <!doctype html>
    #         <title>Upload new File</title>
    #         <h1>Upload new File</h1>
    #         <form method=post enctype=multipart/form-data>
    #           <input type=file name=file>
    #           <input type=submit value=Upload>
    #         </form>
    #         '''


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
app.debug = True
