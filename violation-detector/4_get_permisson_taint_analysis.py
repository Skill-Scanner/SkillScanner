import csv
import json
from tqdm import tqdm
from collections import deque


class Graph:
    def __init__(self, edges, n):
        self.adjList = [[] for _ in range(n)]
        for (src, dest) in edges:
            self.adjList[src].append(dest)


def isReachable(graph, src, dest, discovered, path):
    discovered[src] = True
    path.append(src)
    if src == dest:
        return True
    for i in graph.adjList[src]:
        if not discovered[i]:
            if isReachable(graph, i, dest, discovered, path):
                return True
    path.pop()
    return False


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


def get_all_flow(filename):
    flows = []
    with open(filename) as f:
        reader = csv.reader(f, delimiter = '\n', quoting=csv.QUOTE_NONE)
        lines = list(reader)
        line_number = len(lines)
#        with tqdm(total = line_number) as pbar:
        for rows in lines:
#                x = pbar.update(1)
            for row in rows:
                try:
                    source, sink = row.replace('""', '"').split('source: ')[1].split('"warning","')[0].split('","/')[0].split(' \t sink: ')
                    flows.append((source, sink))
                except:
                    continue
    return flows


def get_slot_from_flow(skill, flows):
    slot_flows = []
    slots = []
    for flow in flows:
        source, sink = flow
        name, location = source[3:-3].split('"|"relative:///')
        if name.endswith('slots'):
            if source not in slots:
                slots.append(source)
                slot_flows.append(flow)
        if name.startswith('Alexa.') or name.startswith('getSlot'):
            code = get_code_content(skill, location)
            if 'getSlotValue' in code:
                slots.append(source)
    return list(set(slots))


def get_address_edges_from_flow(flows):
    new_flow = []
    for flow in flows:
        source, sink = flow
        name, location = source[3:-3].split('"|"relative:///')
        file1, line1, _, _, _ = location.split(':')
        if 'deviceA ... Address' == name:
            for flow2 in flows:
                source2, sink2 = flow2
                name2, location2 = source2[3:-3].split('"|"relative:///')
                file2, line2, _, _, _ = location2.split(':')
                if file1 == file2 and line1 == line2:
                    if 'await d ... viceId)' == name2:
                        new_flow.append((source, source2))
        if 'serviceClientFactory' == name:
            for flow2 in flows:
                source2, sink2 = flow2
                name2, location2 = source2[3:-3].split('"|"relative:///')
                file2, line2, _, _, _ = location2.split(':')
                if file1 == file2 and line1 == line2:
                    if 'handler ... lient()' == name2:
                        new_flow.append((source, source2))   
        if 'context' == name:
            for flow2 in flows:
                source2, sink2 = flow2
                name2, location2 = source2[3:-3].split('"|"relative:///')
                file2, line2, _, _, _ = location2.split(':')
                if file1 == file2 and line1 == line2:
                    if 'request ... context' == name2:
                        new_flow.append((source, source2))                           
    flows = flows + list(set(new_flow))
    return flows


def is_false_nodes(node):
    start_line, start_column, end_line, end_column = node.split(':')[1:5]
    if int(start_line) > int(end_line):
        return True
    elif int(start_line) == int(end_line):
        if int(start_column) >= int(end_column):
            return True
        else:
            return False
    else:
        return False


def get_edges(flows):
    nodes_to_number = {}
    number_to_nodes = {}
    edges = []
    for flow in flows:
        source, sink = flow
        source_name, source_location = source[3:-3].split('"|"relative:///')
        sink_ame, sink_location = sink[3:-3].split('"|"relative:///')
        source = source_location
        sink = sink_location
        if is_false_nodes(source) or is_false_nodes(sink):
            continue
        if source not in nodes_to_number:
            nodes_to_number[source] = len(nodes_to_number)
            number_to_nodes[len(number_to_nodes)] = source
        if sink not in nodes_to_number:
            nodes_to_number[sink] = len(nodes_to_number)
            number_to_nodes[len(number_to_nodes)] = sink
        edges.append((nodes_to_number[source], nodes_to_number[sink]))
    return nodes_to_number, number_to_nodes, edges 


def get_code_content(skill, flow_node):
    location = flow_node.split(':')
    filename = skill.replace('~', '/') + '/' + location[0]
    with open(filename) as f:
        codes = f.read().split('\n')[:-1]
        content = codes[int(location[1]) - 1][int(location[2]) -1 : int(location[4])]
        return content


def get_code_content(skill, flow_node):
    location = flow_node.split(':')
    possible_path = []
    possible_path.append(skill.replace('~', '/') + '/' + location[0])
    possible_path.append(skill.replace('~', '/') + '/lambda/' + location[0])
    possible_path.append(skill.replace('~', '/') + '/../lambda/' + location[0])
    possible_path.append((skill.replace('~', '/') + '/' + location[0]).replace('_', ' '))
    possible_path.append((skill.replace('~', '/') + '/lambda/' + location[0]).replace('_', ' '))
    possible_path.append((skill.replace('~', '/') + '/../lambda/' + location[0]).replace('_', ' '))
    for path in possible_path:
        try:
            f = open(path)
            break
        except:
            continue
    codes = f.read().split('\n')[:-1]
    content = codes[int(location[1]) - 1][int(location[2]) -1 : int(location[4])]
    return content


def get_slot_permission_used_in_output(skill, slots_called, slots_asked, output_ask_value, nodes_to_number, number_to_nodes, edges):
    n = len(nodes_to_number)
    graph = Graph(edges, n)
    paths = []
    for slot in slots_called:
        name, location = slot[3:-3].split('"|"relative:///')
        slot = location
        src = nodes_to_number[slot]
        for output in output_ask_value:
            name, location = output[3:-3].split('"|"relative:///')
            output = location
            if output not in nodes_to_number:
                continue
            dest = nodes_to_number[output]
            path = deque()
            discovered = [False] * n
            if isReachable(graph, src, dest, discovered, path):
                paths.append(path)
    slot_names_used = []
    for path in paths:
        for flow_node in path:
            code_content = get_code_content(skill, number_to_nodes[flow_node])
            for slot_name in slots_asked:
                if slot_name.lower() not in code_content.lower():
                    continue
                if slot_name in slot_names_used:
                    continue
                slot_names_used.append(slot_name)
                if slot_names_used == slots_asked:
                    return slots_asked                     
    return slot_names_used


def find_path(source, edges):
    todo = [source]
    done = []
    while todo != []:
        thisnode = todo[0]
        todo.remove(thisnode)
        done.append(thisnode)
        for edge in edges:
            if edge[0] == thisnode:
                if edge[1] in todo or edge[1] in done:
                    continue
                todo.append(edge[1])
    return done


def get_slot_permission_used_in_database(skill, slots_called, slots_asked, databases, nodes_to_number, number_to_nodes, edges):
    n = len(nodes_to_number)
    graph = Graph(edges, n)
    slot_names_used = []
    for slot in slots_called:
        name, location = slot[3:-3].split('"|"relative:///')
        slot = location
        source1 = nodes_to_number[slot]
        for database in databases:
            name, location = database[3:-3].split('"|"relative:///')
            database = location
            try:
                source2 = nodes_to_number[database]
            except:
                continue
            sink1 = find_path(source1, edges)
            sink2 = find_path(source2, edges)
            if len(set(sink1) & set(sink2)) == 0:
                continue
            path = deque()
            discovered = [False] * n
            if isReachable(graph, source1, min(list(set(sink1) & set(sink2))), discovered, path):
                for flow_node in path:
                    code_content = get_code_content(skill, number_to_nodes[flow_node])
                    for slot_name in slots_asked:
                        if slot_name.lower() in code_content.lower():
                            if slot_name not in slot_names_used:
                                slot_names_used.append(slot_name)
        return slot_names_used


def get_slot_permission_used_in_database2(skill, slots_called, slots_asked, databases, nodes_to_number, number_to_nodes, edges):
    slot_names_used = []
    n = len(nodes_to_number)
    graph = Graph(edges, n)
    for slot in slots_called:
        name, location = slot[3:-3].split('"|"relative:///')
        slot = location
        source1 = nodes_to_number[slot]
        sink1 = find_path(source1, edges)
        for sink in sink1:
            code_content = get_code_content(skill, number_to_nodes[sink])
            if 'sessionAttributes' in code_content:
                path = deque()
                discovered = [False] * n
                if isReachable(graph, source1, sink, discovered, path):
                    for flow_node in path:
                        code_content = get_code_content(skill, number_to_nodes[flow_node])
                        for slot_name in slots_asked:
                            if slot_name.lower() in code_content.lower():
                                if slot_name not in slot_names_used:
                                    slot_names_used.append(slot_name)
    return slot_names_used


def get_slot_flow():
    with open('result/intent_data_collection.csv') as f:
        reader = csv.reader(f)
        data_collection_slots = []
        for row in reader:
            data_collection_slots.append(row)
    slots = {}
    for slot in data_collection_slots:
        skill, intent_name, issue, slot_name, slot_type = slot
        if skill in slots:
            slots[skill].append(slot_name)
        else:
            slots[skill] = [slot_name]
    data_collection_slot_skills = []
    for slot in slots:
        data_collection_slot_skills.append((slot, set(slots[slot])))
    for skill in data_collection_slot_skills:
        try:
            skill, slots_asked = skill
            skill = skill.replace('/', '~')
            slots_asked = list(slots_asked)
            slots_called = get_data('result/slot/' + skill + '.csv')
            flows = get_all_flow('result/allflow/' + skill + '.csv')
            if len(flows) > 100000:
                continue
            slots_called = slots_called + get_slot_from_flow(skill, flows)
            output_ask_value = get_data('result/ask_value/' + skill + '.csv')
            databases = get_data('result/database/' + skill + '.csv')
            nodes_to_number, number_to_nodes, edges = get_edges(flows)
            slots_used_output = get_slot_permission_used_in_output(skill, slots_called, slots_asked, output_ask_value, nodes_to_number, number_to_nodes, edges)
            if len(slots_used_output) > 0:
                print(f'{skill} slot {slots_used_output} is used in output')
            if slots_used_output != slots_asked:
                slots_used_database = get_slot_permission_used_in_database(skill, slots_called, slots_asked, databases, nodes_to_number, number_to_nodes, edges)
            if slots_used_output + slots_used_database != slots_asked:
                slots_used_database = slots_used_database + get_slot_permission_used_in_database2(skill, slots_called, slots_asked, databases, nodes_to_number, number_to_nodes, edges)
            if len(slots_used_database) > 0:
                print(f'{skill} slot {slots_used_database} is used in database')
            for slot in slots_asked:
                if slot not in slots_used_output + slots_used_database:
                    print(f'{skill} slot {slot} is not used')
            print('\n')
            del flows
        except:
                continue


def get_permission_flow():
    data_collection_permission_skills = []
    with open('result/permission_ask_skills.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            data_collection_permission_skills.append(row)
    with open('result/permission_not_used.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            data_collection_permission_skills.remove(row)
    permission_mapping = {}
    permission_mapping['alexa::devices:all:address:full:read'] = 'FullAddress'
    permission_mapping['alexa:devices:all:address:country_and_postal_code:read'] = 'CountryAndPostalCode'
    permission_mapping['alexa::profile:name:read'] = 'ProfileName'
    permission_mapping['alexa::profile:given_name:read'] = 'ProfileGivenName'
    permission_mapping['alexa::profile:email:read'] = 'ProfileEmail'
    permission_mapping['alexa::profile:mobile_number:read'] = 'ProfileMobileNumber'
    permission_mapping['alexa::devices:all:geolocation:read'] = 'Geolocation'
    for skill in data_collection_permission_skills:
        skill, permissions = skill
        skill = skill.replace('/', '~')
        permissions_asked = [permission_mapping[i] for i in permissions[2:-2].split('\', \'')]
        try:
            permissions_called = get_data('result/permission/' + skill + '1.csv')
            permissions_called = permissions_called + get_data('result/permission/' + skill + '2.csv')
        except:
            continue
        flows = get_all_flow('result/allflow/' + skill + '.csv')
        flows = get_address_edges_from_flow(flows)
        if len(flows) > 100000:
            continue
        output_ask_value = get_data('result/ask_value/' + skill + '.csv')
        databases = get_data('result/database/' + skill + '.csv')
        nodes_to_number, number_to_nodes, edges = get_edges(flows)
        try:
            permissions_used_output = get_slot_permission_used_in_output(skill, permissions_called, permissions_asked, output_ask_value, nodes_to_number, number_to_nodes, edges)
            if len(permissions_used_output) > 0:
                print(f'{skill} permission {permissions_used_output} is used in output')
            permissions_used_database = get_slot_permission_used_in_database(skill, permissions_called, permissions_asked, databases, nodes_to_number, number_to_nodes, edges)
            permissions_used_database = permissions_used_database + get_slot_permission_used_in_database2(skill, permissions_called, permissions_asked, databases, nodes_to_number, number_to_nodes, edges)
            if len(permissions_used_database) > 0:
                print(f'{skill} permission {permissions_used_database} is used in database')
        except:
            continue
        for permission in permissions_asked:
            if permission not in permissions_used_output + permissions_used_database:
                print(f'{skill} permission {permission} is not used')
        print('\n')


def main():
    get_permission_flow()
    get_slot_flow()


if __name__ == "__main__":
    main()
