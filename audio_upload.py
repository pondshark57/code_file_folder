#flask import
from flask import  Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
#google api imprt
from google.cloud import speech
#
import io
import os
import csv

from main import main_module

credential_path = "./google_stt_json_key/i-melody-358205-b97b3ed8d64b.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

#flask module
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False #flask json 형식에서 한글 깨짐 현상 해결

port_adress = "192.168.1.12"


f = open("Saturi_file.csv", 'r', encoding='utf-8-sig')
Saturi_word = csv.reader(f)
f.close

f = open("No_DB_word_convert.csv", 'r', encoding='utf-8-sig')
No_DB_word_convert = csv.reader(f)
f.close

#사투리 단어 우선도 추가
speech_contexts = []
# Hint Boost. This value increases the probability that a specific
scw_dict = {}
for row in Saturi_word:
    phrases = row[0]
    boost = (int)(row[1])
    if not boost in scw_dict:
        scw_dict[boost] = list()

    scw_dict[boost].append(phrases)

#구글 데이터 베이스에 없는 단어 처리
NoDBWord = []
for row in No_DB_word_convert:
    NoDBWord.append(row)

for key in scw_dict:
    speech_contexts_element = {"phrases": scw_dict[key], "boost": key}
speech_contexts.append(speech_contexts_element)

print(scw_dict)
print(NoDBWord)


#print(speech_contexts)

@app.route('/')
def home_page():
    return render_template('upload.html')

@app.route('/file_upload', methods= ['GET', 'POST'])
def upload_audio():
    global port_adress

    if request.method == 'POST':

        #파일 저장 코
        f = request.files['file']
        #저장할 경로 + 파일명
        file_root = "./uploads/"+secure_filename(f.filename)
        f.save(file_root)

        #저장된 오디오 파일 stt api 적용
        original_text = stt_func(file_root)
        print("original text:" + original_text)

        converted_text = original_text
        converted_text = converted_text.replace('  ', ' ')
        print(converted_text)
        for words in NoDBWord:
            converted_text = converted_text.replace(words[0], words[1])

        print("Converted text:" + converted_text)

        translated_text = main_module(converted_text)
        #나온 텍스트를 return
        return jsonify(text=converted_text, text2=translated_text)

    elif request.method == 'GET':
        return render_template('upload.html')

#stt api module
client = speech.SpeechClient()
def stt_func(fileName):
    # The name of the audio file to transcribe
    file_name = fileName
    # Loads the audio into memory
    with io.open(file_name, 'rb') as audio_file:
        content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)

    global speech_contexts

    config = {
        "speech_contexts": speech_contexts,
        "sample_rate_hertz": 44100,
        "audio_channel_count" : 2,
        "language_code": 'ko-KR',
        "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
    }

    # Detects speech in the audio file
    response = client.recognize(config=config, audio=audio)

    result_text = []
    for result in response.results:
        result_text.append(result.alternatives[0].transcript)
        # print('Transcript: {}'.format(result.alternatives[0].transcript))

    return_text = ' '
    for text in result_text:
        return_text = return_text + ' ' + text
    return_text = return_text.strip()

    return return_text


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
