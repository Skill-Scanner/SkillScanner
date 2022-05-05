import os
import json
import csv
from tqdm import tqdm
from interruptingcow import timeout
import subprocess


def generate_skill_database_command(original_skill_name, skill_name, skill_type):
    command = ""
    command = command + root_path + "codeql-home/codeql"
    command = command + " database create --language=" + skill_type
    command = command + " --source-root " + root_path + original_skill_name 
    command = command + " " + root_path + "databases/database_" + skill_name
    return command


def generate_output_command(skill_name, skill_type):
    command = ""
    command = command + root_path + "codeql-home/codeql"
    command = command + " database analyze \"" + root_path + "databases/database_" + skill_name + "\""
    command = command + " --rerun " + root_path + "vscode-codeql-starter/codeql-custom-queries-" + skill_type + "/code/get_output.ql"
    command = command + " --format=csv --output=" + root_path + "result/output/" + skill_name + ".csv"
    return command


def generate_flow_command(skill_name, skill_type):
    command = ""
    command = command + root_path + "codeql-home/codeql"
    command = command + " database analyze \"" + root_path + "databases/database_" + skill_name + "\""
    command = command + " --rerun " + root_path + "vscode-codeql-starter/codeql-custom-queries-" + skill_type + "/code/get_flow.ql"
    command = command + " --format=csv --output=" + root_path + "result/allflow/" + skill_name + ".csv"
    return command


def generate_permission_command(skill_name, skill_type, times):
    command = ""
    command = command + root_path + "codeql-home/codeql"
    command = command + " database analyze \"" + root_path + "databases/database_" + skill_name + "\""
    command = command + " --rerun " + root_path + "vscode-codeql-starter/codeql-custom-queries-" + skill_type + "/code/get_permission_" + times + ".ql"
    command = command + " --format=csv --output=" + root_path + "result/permission/" + skill_name + times + ".csv"
    return command


def generate_database_command(skill_name, skill_type):
    command = ""
    command = command + root_path + "codeql-home/codeql"
    command = command + " database analyze \"" + root_path + "databases/database_" + skill_name + "\""
    command = command + " --rerun " + root_path + "vscode-codeql-starter/codeql-custom-queries-" + skill_type + "/code/get_database.ql"
    command = command + " --format=csv --output=" + root_path + "result/database/" + skill_name + ".csv"
    return command


def generate_slot_command(skill_name, skill_type):
    command = ""
    command = command + root_path + "codeql-home/codeql"
    command = command + " database analyze \"" + root_path + "databases/database_" + skill_name + "\""
    command = command + " --rerun " + root_path + "vscode-codeql-starter/codeql-custom-queries-" + skill_type + "/code/get_slot.ql"
    command = command + " --format=csv --output=" + root_path + "result/slot/" + skill_name + ".csv"
    return command


def generate_ask_value_command(skill_name, skill_type):
    command = ""
    command = command + root_path + "codeql-home/codeql"
    command = command + " database analyze \"" + root_path + "databases/database_" + skill_name + "\""
    command = command + " --rerun " + root_path + "vscode-codeql-starter/codeql-custom-queries-" + skill_type + "/code/get_ask_value.ql"
    command = command + " --format=csv --output=" + root_path + "result/ask_value/" + skill_name + ".csv"
    return command


def run_command(skills, run_type):
    with tqdm(total = len(skills)) as pbar:
        for skill in skills:
            x = pbar.update(1)
#            skill_location = skill["root"]
#            original_skill_name = skill_location.replace(root_path, "")
            original_skill_name = skill["code_folder"].replace(root_path, "").replace(" ", "\ ")
            skill_name = skill["root"].replace(root_path, "").replace("/", "~")
            file_types = (set([file.split('.')[-1] for file in skill["code_files"]]))
            if "js" in file_types:
                skill_type = "javascript"
            elif "py" in file_types:
                skill_type = "python"
#            if skill_type == "javascript":
#                continue
            if run_type == "skill_database":
                command = generate_skill_database_command(original_skill_name, skill_name, skill_type)
            if run_type == "output":
                command = generate_output_command(skill_name, skill_type)
            if run_type == "permission":
                command = generate_permission_command(skill_name, skill_type, "1")
                x = os.system(command + " > /dev/null")
                command = generate_permission_command(skill_name, skill_type, "2")
            if run_type == "database":
                command = generate_database_command(skill_name, skill_type)
            if run_type == "slot":
                command = generate_slot_command(skill_name, skill_type)
            if run_type == "ask_value":
                command = generate_ask_value_command(skill_name, skill_type)
            x = os.system(command + " > /dev/null")



def generate_flow(skills):
    with tqdm(total = len(skills)) as pbar:
        for skill in skills:
            x = pbar.update(1)
            skill_location = skill["root"]
            original_skill_name = skill_location.replace(root_path, "")
            skill_name = original_skill_name.replace("/", "~")
            file_types = (set([file.split('.')[-1] for file in skill["code_files"]]))
            if "js" in file_types:
                skill_type = "javascript"
            elif "py" in file_types:
                skill_type = "python"
            command = generate_flow_command(skill_name, skill_type)
            try:
                try:
                    with timeout(60, exception = RuntimeError):
                        p = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        out, err = p.communicate()
                        with open('log_flow.txt', 'a') as f:
                            x = f.write(skill['root'] + '\t' + out.replace('\n', '') + '\t' + str(err) + '\n')
                except RuntimeError:
                    continue
            except:
                continue


def get_data_collection_skills():
    with open('result/intent_data_collection.csv') as f:
        reader = csv.reader(f)
        data_collection_slots = []
        for row in reader:
            data_collection_slots.append(row)
    data_collection_skills = [slot[0].replace(root_path, '') for slot in data_collection_slots]
    with open('result/permission_ask_skills.csv') as f:
        reader = csv.reader(f)
        data_collection_permissions = []
        for row in reader:
            data_collection_permissions.append(row)
    data_collection_skills = set(data_collection_skills + [permission[0] for permission in data_collection_permissions])
    return data_collection_skills


def main():

    skills = [json.loads(i) for i in open(root_path + "skills.json").read().split("\n")[:-1]]



    #    run_command(skills, "skill_database")

    #    run_command(skills, "output")

    run_command(skills, "permission")

    #run_command(skills, "database")

    run_command(skills, "slot")

    run_command(skills, "ask_value")

    generate_flow(skills)




if __name__ == "__main__":
    main()

