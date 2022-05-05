import csv
import os
import json

noun_one_word = open('noun_one_word.txt').read().split('\n')[:-1]
noun_two_word = open('noun_two_word.txt').read().split('\n')[:-1]
unique_noun = ['user', 'name', 'person']


def get_intents(code):
    if 'intents' in code.keys():
        intents = code['intents']
    if 'languageModel' in code.keys():
        intents = code['languageModel']['intents']
    if 'interactionModel' in code.keys():
        intents = code['interactionModel']['languageModel']['intents']
    results = []
    for intent in intents:
        if 'slots' in intent:
            try:
                name = intent['name']
            except:
                name = intent['intent']
            try:
                samples = intent['samples']
            except:
                samples = ""           
            if 'samples' in intent:
                results.append((name, intent['slots'], samples))
            else:
                results.append((name, intent['slots'], ""))
    return results


def spit_slot_name(slot):
    if 'AMAZON' in slot:
        slot = slot.replace('AMAZON.', '')
    if slot.isupper() or '_' in slot:
        words = slot.lower().split('_')
    else: 
        words = []
        word = ''
        for i in slot:
            if i.islower():
                word = word + i
            else:
                words.append(word.lower())
                word = i
        words.append(word.lower())
        if words[0] == '':
            words = words[1:]
    return words


def get_data_collection_slots(slots):
    data_collection_slots = []
    for slot in slots:
        slot_name_words = spit_slot_name(slot['name'])
        if len(set(noun_one_word) & set(slot_name_words)) > 0:
            data_collection_slots.append(slot)
        if any (word in ' '.join(slot_name_words) for word in noun_two_word):
            data_collection_slots.append(slot)
        if len(slot_name_words) == 1 and slot_name_words[0] in unique_noun:
            data_collection_slots.append(slot)   
        if 'type' not in slot:
            continue
        slot_name_words = spit_slot_name(slot['type'])
        if  len(set(noun_one_word) & set(slot_name_words)) > 0:
            data_collection_slots.append(slot)
        if any (word in ' '.join(slot_name_words) for word in noun_two_word):
            data_collection_slots.append(slot)
        if len(slot_name_words) == 1 and slot_name_words[0] in unique_noun:
            data_collection_slots.append(slot)
    return data_collection_slots


def get_slot_collected_data_type(slot):
    slot_name_words = spit_slot_name(slot['name'])
    if len(set(noun_one_word) & set(slot_name_words)) > 0:
        data_type = list(set(noun_one_word) & set(slot_name_words))[0]
    for word in noun_two_word:
        if word in ' '.join(slot_name_words):
            data_type = word
    if len(slot_name_words) == 1 and slot_name_words[0] in unique_noun:
        data_type =  slot_name_words[0]
    if 'type' not in slot:
        return data_type
    slot_name_words = spit_slot_name(slot['type'])
    if len(set(noun_one_word) & set(slot_name_words)) > 0:
        data_type = list(set(noun_one_word) & set(slot_name_words))[0]
    for word in noun_two_word:
        if word in ' '.join(slot_name_words):
            data_type = word
    if len(slot_name_words) == 1 and slot_name_words[0] in unique_noun:
        data_type = slot_name_words[0]
    return data_type


def get_data_collection_intents(slot_samples):         ## whether answer in intent sample 1 have 2 not 3 not sure 4 mix
    intents = {}
    for result in slot_samples:
        skill, intent_name, slot, sample = result
        index = skill + '~' + intent_name
        if index not in intents:
            intents[index] = {}
        if slot['name'] not in intents[index]:
            intents[index][slot['name']] = []
        if sample == "":
            intents[index][slot['name']].append((slot, -1, sample))
        elif sample == '{' + slot['name'] + '}':
            intents[index][slot['name']].append((slot, 2, sample))
        elif 'my' in sample.lower():                                        # this is too simple
            intents[index][slot['name']].append((slot, 1, sample))
        else:
            intents[index][slot['name']].append((slot, 0, sample))
    data_collection_intents = {}
    for i in intents:
        data_collection_intents[i] = []
        for slot in intents[i]:
            values = [j[1] for j in intents[i][slot]]
            if -1 in values:
                data_collection_intents[i].append((intents[i][slot][0][0], -1))
            elif 1 in values:
                data_collection_intents[i].append((intents[i][slot][0][0], 1))
            elif 0 in values:
                data_collection_intents[i].append((intents[i][slot][0][0], 0))
            else:
                data_collection_intents[i].append((intents[i][slot][0][0], 2))
    return data_collection_intents


def read_output_data_collection_result():
    with open( root_path + 'result/output_data_collection.csv') as f:
        reader = csv.reader(f)
        data_collection = []
        for row in reader:
            if row not in data_collection:
                data_collection.append(row)
    return data_collection


def get_slot_samples(skills):
    slot_samples = []
    for skill in skills:
        try:
            code = json.loads(open(skills[skill]['intent_file']).read())
        except:
            continue
        intents = get_intents(code)
        for intent in intents:
            intent_name, slots, samples = intent
            data_collection_slots = get_data_collection_slots(slots)
            for data_collection_slot in data_collection_slots:
                k = 0
                if 'samples' in data_collection_slot:
                    for sample in data_collection_slot['samples']:
                        slot_samples.append((skill, intent_name, data_collection_slot, sample))
                        k = k + 1
                for sample in samples:
                    if '{' + data_collection_slot['name'] + '}' in sample:
                        slot_samples.append((skill, intent_name, data_collection_slot, sample))
                        k = k +1
                if k == 0:
                    slot_samples.append((skill, intent_name, data_collection_slot, ""))
    return slot_samples


def get_intent_issues(data_collection_intents, data_collection_skills):
    data_collection_intents_outputs = []
    data_collection_intents_no_samples = []
    data_collection_intents_no_outputs = []
    data_collection_no_intents_with_outputs = []
    output_skill_done = []
    output_done = {}
    slot_done ={}
    for skill_intent in data_collection_intents:
        skill, intent = skill_intent.split('~')
        filename = skill.replace(root_path, '').replace('/', '~') + '.csv'
        if os.path.exists( 'result/output/' + filename) == False:
            continue
        for slot in data_collection_intents[skill_intent]:
            slot, slot_issue = slot
            if slot_issue == 0:
                continue
            data_type = get_slot_collected_data_type(slot)
            if data_type == 'person':
                data_type = 'name'
    #        if 'name' in data_type:
    #            data_type = 'name'
            if filename in data_collection_skills:
                for output in data_collection_skills[filename]:
                    if output[2][13:] in data_type:
                        if (skill, intent, slot, slot_issue) not in data_collection_intents_outputs:
                            data_collection_intents_outputs.append((skill, intent, slot, slot_issue))
                        output_done[(output[0], output[1], output[2])] = 1
                        slot_done[(skill, intent, slot['name'])] = 1
                if (skill, intent, slot['name']) not in slot_done:
                    data_collection_intents_no_outputs.append((skill, intent, slot, slot_issue))
                output_skill_done.append(filename)
            else:
                if (skill, intent, slot, slot_issue) not in data_collection_intents_no_outputs:
                    data_collection_intents_no_outputs.append((skill, intent, slot, slot_issue))
        if filename not in data_collection_skills:
            continue

    for skill_intent in data_collection_intents:
        skill, intent = skill_intent.split('~')
        filename = skill.replace(root_path, '').replace('/', '~') + '.csv'
        if filename not in data_collection_skills:
            continue
        for output in data_collection_skills[filename]:
            if 'permission' in output[1]:
                continue
            if (output[0], output[1], output[2]) not in output_done:
                data_collection_no_intents_with_outputs.append(output)

    for i in data_collection_intents_outputs + data_collection_intents_no_outputs:
        if i[3] == -1:
            data_collection_intents_no_samples.append(i)

    for i in data_collection_skills:
        if i not in output_skill_done:
            for output in data_collection_skills[i]:
                data_collection_no_intents_with_outputs.append(output)

    #    print(len(data_collection_no_intents_with_outputs))
        write_result(data_collection_intents_outputs, "intent_data_collection")
        write_result(data_collection_intents_no_samples, "intent_without_samples")
        write_result(data_collection_intents_no_outputs, "intent_without_outputs")
        write_result_output(data_collection_no_intents_with_outputs, "output_no_intent_from_intent")


'''

len(set([i[0] for i in data_collection_intents_outputs]))
len(set([i[0] for i in data_collection_intents_no_samples]))
len(set([i[0] for i in data_collection_intents_no_outputs]))
len(set([i[0] for i in data_collection_no_intents_with_outputs]))

'''


# 1: do collect data (answer: my name is {name}) 
# 2: might collect data {name} 
# -1: no sample


def write_result(results, filename):
    with open( root_path + 'result/' + filename + '.csv', 'w', newline = '') as csvfile:
        fieldnames = ['filename', 'intentname', 'slot_issue', 'slot_name', 'slot_type']
        writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
        for result in results:
            x = writer.writerow({'filename': result[0].replace(root_path, ''), 'intentname': result[1], 'slot_issue': result[3], 'slot_name': result[2]['name'] , 'slot_type': result[2]['type']})


def write_result_output(results, filename):
    with open( root_path + 'result/' + filename + '.csv', 'w', newline = '') as csvfile:
        fieldnames = ['filename', 'output', 'data']
        writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
        for result in results:
            x = writer.writerow({'filename': result[0].replace(root_path, ''), 'output': result[1], 'data': result[2]})



def main():

    skills = [json.loads(i) for i in open('skills.json').read().split('\n')[:-1]]
    test = {}
    for skill in skills:
        test[skill['root'].replace(' ','_')] = skill

    skills = test

    slot_samples = get_slot_samples(skills)
    data_collection_intents = get_data_collection_intents(slot_samples)
    data_collection_outputs = read_output_data_collection_result()

    data_collection_skills = {}
    for line in data_collection_outputs:
        try:
            data_collection_skills[line[0]].append(line)
        except:
            data_collection_skills[line[0]] = [line]

    get_intent_issues(data_collection_intents, data_collection_skills)



if __name__ == "__main__":
    main()


