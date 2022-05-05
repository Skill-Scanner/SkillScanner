## get palmetto output

import os
import re
import csv
import json
import string
import subprocess
from tqdm import tqdm
from bs4 import BeautifulSoup
from interruptingcow import timeout
import spacy
nlp = spacy.load("en_core_web_sm")



def get_data_collection(outputs):
    noun = [ 'address', 'name', 'email', 'email address', 'birthday', 'age', 'gender', 'location', 'contact', 'phonebook', 'profession', 'income', 'ssn', 'zipcode', 'ethnicity', 'affiliation', 'orientation', 'affiliation', 'postal code', 'zip code', 'first name', 'last name', 'full name', 'phone number', 'social security number', 'passport number', 'driver license', 'bank account number', 'debit card numbers']
    noun2 = [word.split()[-1] for word in noun]
    add_sentences = {"how old are you": 'age', "when were you born": 'age', "where do you live":'location' ,"where are you from": 'location', "what can i call you": 'name', 'male or female': 'gender'}
    skills = []
    with tqdm(total = len(outputs)) as pbar:
        for output in outputs:
            file, output = output
            x  = pbar.update(1)
            if 'your' not in output:
                continue
            if ' ' not in output:
                continue
            if len(output) > 1000:
                continue
            if output[0:4] == 'here':
                continue
            if 'jesus' in output:
                continue
            sentences = re.split(r' *[\n\,\.!][\'"\)\]]* *', output)
            for sentence in sentences:
                if 'here\'s what you need to know' in sentence:
                    continue
                if 'your name is' in sentence:
                    continue
                if any (word in sentence for word in noun) and 'your' in sentence:
                    doc = nlp(sentence)
                for word in noun:
                    if word not in sentence or 'your' not in sentence:
                        continue
                    if word == 'name' and 'your name' not in sentence:
                        continue
                    if word == 'address' and 'email address' in sentence:
                        continue
                    if word == 'phone number' and 'dial your local emergency' in sentence:
                        continue
                    for l in doc:
                        if l.text == 'your' and l.head.text in noun2 and l.head.text in word:
                            if 'name' in word:
                                skills.append((file, output, 'collect data name'))
                            else:
                                skills.append((file, output, 'collect data ' + word))
                for sent in add_sentences:
                        if sent in sentence.translate(str.maketrans('', '', string.punctuation)):
                            skills.append((file, output, 'collect data ' + add_sentences[sent]))
    return skills


def get_sensitive_data_collection(outputs):
    sensitive_data = []
    sensitive_data.append('passport number')
    sensitive_data.append('social security number')
    sensitive_data.append('national identity number')
    sensitive_data.append('bank account number')
    sensitive_data.append('credit card number')
    sensitive_data.append('debit card number')
    sensitive_data.append('driver license number')
    sensitive_data.append('vehicle registration number')
    sensitive_data.append('insurance policy number')
    results = []
    for output in outputs:
        if any (data in output[1] for data in sensitive_data):
            results.append(output)
    return results


## here need a version about output for sentence (have space, longer than 10), ignore websites and others
def get_cleaned_data(filename):
    outputs = []
    try:
        with open(filename) as f:
            reader = csv.reader(f)
            for row in reader:
                if row[3] != ' ' and ' ' in row[3]:
                    outputs.append(row)
    except:
        with open(filename) as f:
            reader = csv.reader((line.replace('\0','') for line in f), delimiter=",")
            for row in reader:
                if row[3] != ' ' and ' ' in row[3]:
                    outputs.apped(row)
    files = {}
    for output in outputs:
        if output[4] in files:
            files[output[4]] = files[output[4]] + 1
        else:
            files[output[4]] = 1
    file_for_data = []
    for file in files:
        if files[file] > 1000:
            file_for_data.append(file)
    cleaned_outputs = []
    for output in outputs:
        if output[4] in file_for_data:
            continue
        cleaned_outputs.append(output)
    return cleaned_outputs    


def get_data(filename):
    outputs = []
    try:
        with open(filename) as f:
            reader = csv.reader(f)
            for row in reader:
                if row[4].endswith('.py') or row[4].endswith('.js'):
                    outputs = outputs + row[3].split('\n')
    except:
        with open(filename) as f:
            reader = csv.reader((line.replace('\0','') for line in f), delimiter=",")
            for row in reader:
                if row[4].endswith('.py') or row[4].endswith('.js'):
                    outputs = outputs + row[3].split('\n')
    return outputs


def write_all_output_data():
    location = root_path + "result/output/"
    files = os.listdir(location)
    with open( root_path + 'result/output_all.csv', 'w', newline = '') as csvfile:
        fieldnames = ['filename', 'output']
        writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
        writer.writeheader()
        with tqdm(total = len(files)) as pbar:
            for file in files:
                x = pbar.update(1)
                results = get_data(location + file)
                for result in results:
                    x = writer.writerow({ 'filename': file, 'output': result})


def write_output_data_collection_result():
    with open(root_path + 'result/output_all.csv') as f:
        reader = csv.reader(f)
        outputs = []
        for row in reader:
            outputs.append(row)
        data_colletion = get_data_collection(outputs)
        with open( root_path + 'result/output_data_collection.csv', 'a', newline = '') as csvfile:
            fieldnames = ['filename', 'output', 'type']
            writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
            writer.writeheader()
            for i in data_colletion:
                x = writer.writerow({ 'filename': i[0], 'output': i[1], 'type': i[2]})
        del data_colletion


def read_output_data_collection_result():
    with open( root_path + 'result/output_data_collection.csv') as f:
        reader = csv.reader(f)
        data_collection = []
        for row in reader:
            if row not in data_collection:
                data_collection.append(row)
    return data_collection


def get_privacy_policy_link(publish):
    if 'manifest' in publish:
        content = publish['manifest']
    else:
        content = publish['skillManifest']
    try:
        privacy_policy = content['privacyAndCompliance']['locales']['en-US']['privacyPolicyUrl']
    except:
        privacy_policy = ""
    return privacy_policy


def get_privacy_policy_content(privacy_policy_link):
    if privacy_policy_link.replace('/', '~') not in os.listdir('privacy_policy/'):
        try:
            try:
                with timeout(60, exception = RuntimeError):
                    command = 'curl -L "' + privacy_policy_link + '" >' + 'privacy_policy/' + privacy_policy_link.replace('/', '~')
                    p = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    out, err = p.communicate()
            except RuntimeError:
                return ""
        except:
            return ""
    content = open('privacy_policy/' + privacy_policy_link.replace('/', '~'))
    soup = BeautifulSoup(content, features="html.parser")
    for script in soup(["script", "style"]):
        x = script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    content = '\n'.join(chunk for chunk in chunks if chunk)
    return content.lower()


def write_result(results):
    with open( root_path + 'result/output_data_collection_violation.csv', 'w', newline = '') as csvfile:
        fieldnames = ['filename', 'data_type', 'violation', 'output']
        writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
        writer.writeheader()
        for result in results:
            x = writer.writerow({ 'filename': result[0].replace('~', '/'), 'data_type': result[3], 'violation': result[1], 'output': result[2]})


def main():

    # write_all_output_data()

    # write_output_data_collection_result()

    skills = [json.loads(i) for i in open('skills.json').read().split('\n')[:-1]]
    test = {}
    for skill in skills:
        test[skill['root']] = skill

    skills = test


    data_collection = read_output_data_collection_result()
    data_collection_skills = {}
    for skill in data_collection:
        try:
            data_collection_skills[skill[0][:-4]].append(skill)
        except:
            data_collection_skills[skill[0][:-4]] = [skill]


    results = []
    for skill in data_collection_skills:
        try:
            publish = json.loads(open(skills[(root_path + skill.replace('~', '/'))]['publish_file']).read())
            privacy_policy_link = get_privacy_policy_link(publish)
            content = get_privacy_policy_content(privacy_policy_link)
        except:
            for i in data_collection_skills[skill]:
    #            print( i[0] + '\t' + 'lack a privacy policy' + '\t' + i[1] + '\t' + i[2])
                results.append((i[0], 'lack a privacy policy', i[1], i[2]))
            continue
        for i in data_collection_skills[skill]:
            if i[2][13:] not in content:
    #            print( i[0] + '\t' + 'incomplete privacy policy' + '\t' + i[1] + '\t' + i[2])
                results.append((i[0], 'incomplete privacy policy', i[1], i[2]))

    write_result(results)



if __name__ == "__main__":
    main()
