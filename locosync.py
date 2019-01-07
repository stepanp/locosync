import sys
import os
import os.path
import json
import io

def main(args):
    print("Load config...")

    if len(args) < 2:
        print("Localization source dir is unspecified")
        sys.exit()

    source_dir = args[1]

    config_path = source_dir + "/localization.json"
    if not os.path.isfile(config_path):
        print(source_dir + " is not localization source dir")
        sys.exit()

    config = parse_config(config_path, source_dir)
    languages = map(lambda l: l[:-len(".json")], filter(lambda l: l != "localization.json" and l.endswith("json"), os.listdir(source_dir)))

    if "ios_path" in config:
        print("Process iOS localization...")
        process_languages("ios", languages, source_dir, config["ios_path"])
        pass

    if "android_path" in config:
        print("Process Android localization...")
        process_languages("android", languages, source_dir, config["android_path"])

    print("Done")

def parse_config(path, source_dir):
    with open(path) as data:
        json_config = json.load(data)

    return {
        "ios_path" : os.path.abspath(source_dir + "/" + json_config["ios_path"]) if "ios_path" in json_config else None,
        "android_path" : os.path.abspath(source_dir + "/" + json_config["android_path"]) if "android_path" in json_config else None,
    }

def process_languages(platform, languages, source_dir, output_path):
    transform = globals()["transform_" + platform]
    save = globals()["save_" + platform]

    for lang in languages:
        print(lang)

        lang_json = load_language(lang, source_dir)
        save(lang, output_path, transform(lang_json))

def load_language(lang, source_dir):
    path = source_dir + "/" + lang + ".json"

    with open(path) as data:
        return json.load(data)

def filter_platform(strings_json, platform, exclude_platforms):
    strings = {}

    def is_excluded(key):
        for exclude in exclude_platforms:
            if key.endswith("_" + exclude):
                return True

    for key, value in strings_json.iteritems():

        if is_excluded(key):
            continue

        if key.endswith("_" + platform):
            strings[key[:-len("_" + platform)]] = escape_symbols(value)
            continue

        if key in strings:
            continue

        strings[key] = escape_symbols(value)

    return strings

def escape_symbols(value):
    value = value.replace("\n", "\\n")
    value = value.replace("\"", "\\\"")

    return value

def transform_ios(strings_json):
    strings = filter_platform(strings_json, "ios", ["android"])

    for key, value in strings.iteritems():
        strings[key] = value.replace("%s", "%@")

    lines = []
    lines.append("/* THIS FILE IS AUTOMATICALLY GENERATED BY LOCALIZATION TOOL */")
    lines.append("/* DO NOT EDIT MANUALLY */")

    for key, value in sorted(strings.iteritems()):
        lines.append("\"" + key + "\" = \"" + value + "\";")

    return lines

def transform_android(strings_json):
    strings = filter_platform(strings_json, "android", ["ios"])

    lines = []
    lines.append("<!-- THIS FILE IS AUTOMATICALLY GENERATED BY LOCALIZATION TOOL -->")
    lines.append("<!-- DO NOT EDIT MANUALLY -->")
    lines.append("<resources>")

    for key, value in sorted(strings.iteritems()):
        lines.append("	<string name=\"" + key + "\">" + value + "</string>")

    lines.append("</resources>")

    return lines

def save_ios(lang, path, strings):
    output_path = path + "/" + lang + ".lproj/Localizable.strings"
    save_file(output_path, strings)

def save_android(lang, path, strings):
    if lang == "en":
        output_path = path + "/values/strings.xml"
    else:
        output_path = path + "/values-" + lang + "/strings.xml"

    save_file(output_path, strings)

def save_file(output_path, strings):
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    with io.open(output_path, 'w', encoding="utf-8") as file:
        file.write("\n".join(strings))

main(sys.argv)