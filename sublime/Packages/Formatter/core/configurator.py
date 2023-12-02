#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# @rev          74a48aa645ba5e1955cd3e50c8e141a300ddc6f5 (74a48aa)
# @tree         0de149c628a1cd9f2ad0786bc9863e7125aa41ad (0de149c)
# @date         2023-11-27 05:08:37 +0100
# @author       bitst0rm <bitst0rm@users.noreply.github.com>
# @copyright    Copyright (c) 2019-present, Duc Ng. (bitst0rm)
# @link         https://github.com/bitst0rm
# @license      The MIT License (MIT)

import re
import uuid
import json
import logging
import sublime
from collections import OrderedDict
from . import common
from ..modules import __all__ as formatter_map

log = logging.getLogger(__name__)


class NoIndent(object):
    def __init__(self, value):
        self.value = value


class NoIndentEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kwargs = dict(kwargs)
        del self.kwargs['indent']
        self._replacement_map = {}

    def default(self, o):
        if isinstance(o, NoIndent):
            key = uuid.uuid4().hex
            self._replacement_map[key] = json.dumps(o.value, **self.kwargs)
            return '@@%s@@' % (key,)
        else:
            return super().default(o)

    def encode(self, o):
        result = super().encode(o)
        for k, v in iter(self._replacement_map.items()):
            result = result.replace('"@@%s@@"' % (k,), v)
        return result


def strip_trailing(text):
    return ('\n'.join([line.rstrip() for line in text.split('\n')]))

def build_sublime_menu_children(formatter_map):
    beautifiers = []
    minifiers = []
    converters = []
    custom = []
    type_to_list = {'beautifier': beautifiers, 'minifier': minifiers, 'converter': converters}

    for uid, module_info in formatter_map.items():
        config = getattr(module_info['module'], 'MODULE_CONFIG', None)
        if config:
            child = OrderedDict([
                ('caption', config['name'] + (' (min)' if config['type'] == 'minifier' else '')),
                ('command', 'run_format'),
                ('args', OrderedDict([
                    ('uid', config['uid']),
                    ('type', config['type'])
                ]))
            ])

            target_list = type_to_list.get(config['type'], custom)
            target_list.append(child)

    return beautifiers, minifiers, converters, custom

def build_context_sublime_menu(formatter_map):
    context_menu = [
        OrderedDict([
            ('caption', 'Formatter'),
            ('id', 'formatter'),
            ('children', [
                OrderedDict([
                    ('caption', '☰ Quick Options'),
                    ('command', 'quick_options')
                ])
            ])
        ])
    ]

    beautifiers, minifiers, converters, custom = build_sublime_menu_children(formatter_map)
    sort_and_extend = lambda lst, caption=None: context_menu[0]['children'].extend(
        ([{'caption': caption}] if (caption and lst) else []) + sorted(lst, key=lambda x: x['args']['uid'])
    )
    sort_and_extend(beautifiers, '-')
    sort_and_extend(minifiers, '-')
    sort_and_extend(converters, '-')
    sort_and_extend(custom, '-')

    json_text = json.dumps(context_menu, cls=NoIndentEncoder, ensure_ascii=False, indent=4)
    return strip_trailing(json_text)

def build_main_sublime_menu(formatter_map):
    main_menu = [
        OrderedDict([
            ('caption', 'Tools'),
            ('id', 'tools'),
            ('mnemonic', 'T'),
            ('children', [
                OrderedDict([
                    ('caption', 'Formatter'),
                    ('id', 'formatter'),
                    ('children', [
                        OrderedDict([
                            ('caption', '☰ Quick Options'),
                            ('command', 'quick_options')
                        ])
                    ])
                ])
            ])
        ]),
        OrderedDict([
            ('caption', 'Preferences'),
            ('id', 'preferences'),
            ('mnemonic', 'n'),
            ('children', [
                OrderedDict([
                    ('caption', 'Package Settings'),
                    ('id', 'package-settings'),
                    ('mnemonic', 'P'),
                    ('children', [
                        OrderedDict([
                            ('caption', 'Formatter'),
                            ('children', [
                                OrderedDict([
                                    ('caption', 'Settings'),
                                    ('command', 'edit_settings'),
                                    ('args', OrderedDict([
                                        ('base_file', '${packages}/Formatter/Formatter.sublime-settings'),
                                        ('default', '// Do NOT edit anything in the left-hand pane.\n'
                                                    '// Pick up items you need, but make sure to maintain the structure.\n'
                                                    '{\n\t$0\n}\n')
                                    ]))
                                ]),
                                OrderedDict([
                                    ('caption', 'Open Config Folders'),
                                    ('command', 'open_config_folders')
                                ]),
                                OrderedDict([
                                    ('caption', '-')
                                ]),
                                OrderedDict([
                                    ('caption', 'Example Key Bindings'),
                                    ('command', 'open_file'),
                                    ('args', OrderedDict([
                                        ('file', '${packages}/Formatter/Example.sublime-keymap')
                                    ]))
                                ]),
                                OrderedDict([
                                    ('caption', 'Key Bindings – User'),
                                    ('command', 'open_file'),
                                    ('args', OrderedDict([
                                        ('file', '${packages}/User/Default (${platform}).sublime-keymap')
                                    ]))
                                ]),
                                OrderedDict([
                                    ('caption', '-')
                                ]),
                                OrderedDict([
                                    ('caption', 'Version Info'),
                                    ('command', 'show_version')
                                ])
                            ])
                        ])
                    ])
                ])
            ])
        ])
    ]

    def add_mnemonic_recursive(data, mnemonic_prefix=''):
        for item in data:
            caption = item.get('caption')
            mnemonic = item.get('mnemonic')
            if caption and caption != '-' and mnemonic is None:
                mnemonic_key = 'mnemonic'
                caption_mnemonic = mnemonic_prefix
                for char in caption:
                    if char.isalnum():
                        caption_mnemonic += char
                        break
                item[mnemonic_key] = caption_mnemonic.upper()
                ordered_item = OrderedDict([(key, item[key]) if key in item else (key, None) for key in ['caption', mnemonic_key]])
                ordered_item.update(item)
                item.clear()
                item.update(ordered_item)

            children = item.get('children', [])
            if children:
                add_mnemonic_recursive(children, mnemonic_prefix)

    beautifiers, minifiers, converters, custom = build_sublime_menu_children(formatter_map)
    sort_and_extend = lambda lst, caption=None: main_menu[0]['children'][0]['children'].extend(
        ([{'caption': caption}] if (caption and lst) else []) + sorted(lst, key=lambda x: x['args']['uid'])
    )
    sort_and_extend(beautifiers, '-')
    sort_and_extend(minifiers, '-')
    sort_and_extend(converters, '-')
    sort_and_extend(custom, '-')
    add_mnemonic_recursive(main_menu, mnemonic_prefix='')

    json_text = json.dumps(main_menu, cls=NoIndentEncoder, ensure_ascii=False, indent=4)
    return strip_trailing(json_text)

def build_formatter_sublime_commands_children(formatter_map):
    beautifiers = []
    minifiers = []
    converters = []
    custom = []
    type_to_list = {'beautifier': beautifiers, 'minifier': minifiers, 'converter': converters}
    type_to_action = {'beautifier': 'Beautify', 'minifier': 'Minify', 'converter': 'Convert'}

    for uid, module_info in formatter_map.items():
        config = getattr(module_info['module'], 'MODULE_CONFIG', None)
        if config:
            child = OrderedDict([
                ('caption', 'Formatter: ' + type_to_action.get(config['type'], 'Customize') + ' with ' + config['name']),
                ('command', 'run_format'),
                ('args', OrderedDict([
                    ('uid', config['uid']),
                    ('type', config['type'])
                ]))
            ])

            target_list = type_to_list.get(config['type'], custom)
            target_list.append(child)

    return beautifiers, minifiers, converters, custom

def build_formatter_sublime_commands(formatter_map):
    sublime_commands = [
        OrderedDict([
            ('caption', 'Formatter: Show Version'),
            ('command', 'show_version')
        ]),
        OrderedDict([
            ('caption', 'Formatter: Open Config Folders'),
            ('command', 'open_config_folders')
        ]),
        OrderedDict([
            ('caption', 'Formatter: Quick Options'),
            ('command', 'quick_options')
        ])
    ]

    beautifiers, minifiers, converters, custom = build_formatter_sublime_commands_children(formatter_map)
    sort_and_extend = lambda lst, caption=None: sublime_commands.extend(
        ([{'caption': caption}] if (caption and lst) else []) + sorted(lst, key=lambda x: x['args']['uid'])
    )
    sort_and_extend(beautifiers, None)
    sort_and_extend(minifiers, None)
    sort_and_extend(converters, None)
    sort_and_extend(custom, None)

    json_text = json.dumps(sublime_commands, cls=NoIndentEncoder, ensure_ascii=False, indent=4)
    return strip_trailing(json_text)

def build_example_sublime_keymap(formatter_map):
    beautifiers = []
    minifiers = []
    converters = []
    custom = []
    type_to_list = {'beautifier': beautifiers, 'minifier': minifiers, 'converter': converters}

    for uid, module_info in formatter_map.items():
        config = getattr(module_info['module'], 'MODULE_CONFIG', None)
        if config:
            child = OrderedDict([
                        ('keys', ['ctrl+super+?']),
                        ('command', 'run_format'),
                        ('args', OrderedDict([
                            ('uid', uid),
                            ('type', config['type'])
                        ]))
                    ])

            target_list = type_to_list.get(config['type'], custom)
            target_list.append(child)

    sort_key = lambda x: x['args']['uid']
    sorted_beautifiers, sorted_minifiers, sorted_converters, sorted_custom = [sorted(lst, key=sort_key) for lst in [beautifiers, minifiers, converters, custom]]

    quick_options = '{"keys": ["ctrl+super+?"], "command": "quick_options"},\n    '
    formatted_keymap = '[\n    ' + quick_options + ',\n    '.join([json.dumps(item, cls=NoIndentEncoder, ensure_ascii=False) for item in sorted_beautifiers + sorted_minifiers + sorted_converters + sorted_custom]) + '\n]'

    comment = '''// This example is not ready to use.
// End-users are free to remap any key combination, but keep in mind:
// 1. Ctrl+Alt+<alphanum> should never be used in any Windows key bindings.
// 2. Option+<alphanum> should never be used in any macOS key bindings.
// In both cases, the user's ability to insert non-ASCII characters
// would be compromised otherwise.
//
// Modifiers:
// shift
// ctrl or control
// alt
// super (Windows: Windows key, MacOS: Command Key)
// primary (Windows: Control key, MacOS: Command Key)
// command (MacOS only)
// option (MacOS only: same as alt)

'''

    return strip_trailing(comment + formatted_keymap)

def build_formatter_sublime_settings_children(formatter_map):
    beautifiers = []
    minifiers = []
    converters = []
    custom = []
    type_to_list = {'beautifier': beautifiers, 'minifier': minifiers, 'converter': converters}

    for uid, module_info in formatter_map.items():
        config = getattr(module_info['module'], 'MODULE_CONFIG', None)
        if config:
            child = OrderedDict([
                ('info', config['source']),
                ('disable', False),
                ('format_on_paste', False),
                ('format_on_save', False),
                ('new_file_on_format', False),
                ('recursive_folder_format', OrderedDict([
                    ('enable', False),
                    ('exclude_folders_regex', []),
                    ('exclude_files_regex', []),
                    ('exclude_extensions', []),
                    ('exclude_syntaxes', [])
                ])),
                ('syntaxes', NoIndent(config['syntaxes']))
            ])

            exclude_syntaxes = config.get('exclude_syntaxes', None)
            if exclude_syntaxes is not None and isinstance(exclude_syntaxes, dict):
                child['exclude_syntaxes'] = {key: NoIndent(value) for key, value in exclude_syntaxes.items()}

            executable_path = config.get('executable_path', None)
            if executable_path is not None and isinstance(executable_path, str):
                child['executable_path'] = executable_path

            args = config.get('args', None)
            if args is not None and isinstance(args, list) and len(args) > 0:
                child['args'] = NoIndent(args)

            config_path = config.get('config_path', None)
            if config_path is not None and isinstance(config_path, dict) and len(config_path) > 0:
                child['config_path'] = {key: common.join('${packages}', 'User', common.ASSETS_DIRECTORY, 'config', value) for key, value in config['config_path'].items()}
                default_value = child['config_path'].pop('default', None)
                sorted_config_path = OrderedDict(sorted(child['config_path'].items()))
                if default_value:
                    sorted_config_path['default'] = default_value
                child['config_path'] = sorted_config_path

            comment = config.get('comment', None)
            if comment is not None and isinstance(comment, str) and len(comment) > 0:
                truncated_comment = comment[:80] + '...' if len(comment) > 80 else comment
                child['__COMMENT__child'] = '/* ' + truncated_comment.replace('/*', '').replace('*/', '') + ' */'  # '/* ' is marker for pattern_comma_before_comment

            target_list = type_to_list.get(config['type'], custom)
            target_list.append({uid:child})

    return beautifiers, minifiers, converters, custom

def build_formatter_sublime_settings(formatter_map):
    sublime_settings = OrderedDict([
            ('__COMMENT__debug', '''// Enable debug mode to view errors in the console.'''),
            ('debug', False),
            ('__COMMENT__open_console_on_failure', '''
    // Auto open the console panel whenever formatting failed.
    // This is useful when combined with "debug": true'''),
            ('open_console_on_failure', False),
            ('__COMMENT__show_statusbar', '''
    // Display results in the status bar.
    // The displayed abbreviation for the current settings mode:
    // PUS: Persistent User Settings
    // PQO: Persistent Quick Options
    // TQO: Temporary Quick Options'''),
            ('show_statusbar', True),
            ('__COMMENT__show_words_count', '''
    // Display a real-time word and character count in the status bar.
    // By default, whitespace is not included in the character count.'''),
            ('show_words_count', OrderedDict([
                ('enable', True),
                ('ignore_whitespace_char', True)
            ])),
            ('__COMMENT__remember_session', '''
    // Remember and restore cursor position, selections, selected
    // syntax and bookmarks each time a file is closed and re-opened.
    // This is helpful to resume your work from where you left off.'''),
            ('remember_session', True),
            ('__COMMENT__layout', '''
    // Configure the layout when opening new files.
    // This setting takes effect when the "new_file_on_format" option is enabled.
    // Available choices include 2-columns, 2-rows or single layout.
    // To revert to the Sublime default layout:
    // View > Layout > Single
    // Accepted values: "2cols", "2rows", "single" or false'''),
            ('layout', OrderedDict([
                ('enable', '2cols'),
                ('sync_scroll', True)
            ])),
            ('__COMMENT__environ', '''
    // A set of directories where executable programs are located.
    // It can be absolute paths to module directories, python zipfiles.
    // Any environment variables like PATH, PYTHONPATH, GEM_PATH, TMPDIR etc.
    // can be added here.
    // This option is similar to running 'export PYTHONPATH="/path/to/my/site-packages"'
    // from terminal. But it is only temporary in the memory and will only apply
    // for the current formatting session.
    // Non-existent environment directories and files will be silently ignored.
    // This option can be ommitted, but for python and ruby you probably need
    // to add it, either persistently via ~/.bashrc, ~/.zshrc, ~/.profile or here.'''),
            ('environ', OrderedDict([
                ('PATH', []),
                ('GEM_PATH', []),
                ('PYTHONPATH', [])
            ])),
            ('__COMMENT__formatters', '''
    // THIRD-PARTY FORMATTING PLUGINS'''),
            ('formatters', OrderedDict([
                ('example', OrderedDict([
                    ('__COMMENT__disable', '''// Disable and remove plugin from being shown in the menu.'''),
                    ('disable', False),
                    ('__COMMENT__format_on_save', '''
            // Auto formatting whenever the current file/view is being saved.
            // This option should be used for plugins with unique syntaxes.
            // For plugins with the same syntaxes, the first plugin takes precedence.
            // Remove the identical syntaxes from one of the plugins to avoid conflicts.
            // For example:
            // Plugin A (enabled): syntaxes ["css", "js"]
            // Plugin B (enabled): syntaxes ["html", "css"]
            // In the case you want to use Plugin B with "css", then you should remove
            // the "css" from plugin A or just disable it, as there is no guarantee of the
            // execution order between the two, and determining your favorist is not possible.
            // The Quick Options feature can help in this scenario.'''),
                    ('format_on_save', False),
                    ('__COMMENT__format_on_paste', '''
            // Auto formatting whenever code is pasted into the current file/view.
            // The conditions and solution for this option are identical to those of
            // the "format_on_save" option mentioned above.'''),
                    ('format_on_paste', False),
                    ('__COMMENT__new_file_on_format', '''
            // Create a new file containing formatted codes.
            // The value of this option is the suffix of the new file being renamed.
            // Suffix must be of type string. =true, =false and all other types imply =false
            // Note: It will overwrite any existing file that has the same new name in
            // the same location.
            // For example:
            // "new_file_on_format": "min", will create a new file:
            // myfile.raw.js -> myfile.raw.min.js'''),
                    ('new_file_on_format', False),
                    ('__COMMENT__recursive_folder_format', '''
            // Recursively format the entire folder with unlimited depth.
            // This option requires an existing and currently opened file
            // to serve as the starting point.
            // For the sake of convenience, two new folders will be created at
            // the same level as the file, which will contain all failed and
            // successfully formatted files. The "new_file_on_format" option
            // might be useful for renaming if needed.
            // The "format_on_save" option above, which applies only to
            // single files, does not take effect here.
            // All none-text files (binary) will be automatically ignored.
            // Note: Placing files directly on the Desktop or elsewhere without
            // enclosing them within a folder can lead to accidental formatting.
            // Any literal "$" must be escaped to "\\$" to distinguish it from
            // the variable expansion "${...}". This important rule applies
            // to the entire content of this settings file!'''),
                    ('recursive_folder_format', OrderedDict([
                        ('enable', False),
                        ('exclude_folders_regex', NoIndent(['Spotlight-V100', 'temp', 'cache', 'logs', '^_.*?tits\\$'])),
                        ('exclude_files_regex', NoIndent(['show_tits.sx', '.*?ball.js', '^._.*?'])),
                        ('exclude_extensions', NoIndent(['DS_Store', 'localized', 'TemporaryItems', 'Trashes', 'db', 'ini', 'git', 'svn', 'tmp', 'bak'])),
                        ('exclude_syntaxes', [])
                    ])),
                    ('__COMMENT__syntaxes', '''
            // Syntax support based on the scope name, not file extension.
            // Syntax name is part of the scope name and can be retrieved from:
            // Tools > Developer > Show Scope Name
            // End-users are advised to consult plugin documentation to add more syntaxes.'''),
                    ('syntaxes', NoIndent(['css', 'html', 'js', 'php'])),
                    ('__COMMENT__exclude_syntaxes', '''
            // Exclude a list of syntaxes for an individual syntax key.
            // A list of excluded syntaxes can be applied to all syntax definitions.
            // In this case, the key must be named: "all".
            // This option is useful to exclude part of the scope selector.
            // For example: text.html.markdown, want html but wish to filter out markdown.'''),
                    ('exclude_syntaxes', OrderedDict([
                        ('html', NoIndent(['markdown'])),
                        ('all', NoIndent(['markdown']))
                    ])),
                    ('__COMMENT__interpreter_path', '''
            // Path to the interpreter to run the third-party plugin.
            // Just for the sake of completeness, but it is unlikely that you will ever need
            // to use this option. Most of the programs you have installed are usually set
            // to run in the global environment, such as Python, Node.js, Ruby, PHP, etc.
            // Formatter is able to detect and automatically set them for you.
            // However, if you do need to use a specific interpreter, you can provide the path.'''),
                    ('interpreter_path', '${HOME}/example/path/to\\$my/java.exe'),
                    ('__COMMENT__executable_path', '''
            // Path to the third-party plugin executable to process formatting.
            // System variable expansions like ${HOME} and Sublime Text specific
            // ${packages}, ${file_path} etc. can be used to assign paths. More:
            // https://www.sublimetext.com/docs/build_systems.html#variables
            // Note: Again, any literal "$" must be escaped to "\\$" to distinguish
            // it from the variable expansion "${...}".'''),
                    ('executable_path', '${HOME}/example/path/to\\$my/php-cs-fixer.phar'),
                    ('__COMMENT__config_path', '''
            // Path to the config file for each individual syntaxes.
            // Syntax keys must match those in the "syntaxes" option above.
            // A single config file can be used to assign to all syntaxes.
            // In this case the key must be named: "default"
            // Formatter provides a set of default config files under
            // "formatter.assets/config" folder for your personal use.
            // Do not use the reference files with suffix '.master.' directly.
            // These files could be overwritten by any release updates.'''),
                    ('config_path', OrderedDict([
                        ('css', '${packages}/User/formatter.assets/config/only_css_rc.json'),
                        ('php', '${packages}/User/formatter.assets/config/only_php_rc.json'),
                        ('default', '${packages}/User/formatter.assets/config/css_plus_js_plus_php_rc.json')
                    ])),
                    ('__COMMENT__args', '''
            // Array of additional arguments for the command line.'''),
                    ('args', NoIndent(['--basedir', './example/my/baseball', '--show-tits', 'yes'])),
                    ('__COMMENT__fix_commands', '''
            // Manipulate hardcoded command-line arguments.
            // This option allow you to modify hardcoded parameters, values and
            // their positions without digging into the source code.
            // Note: Hardcoded args can be changed (rarely) by any release updates.
            // Enable debug mode will help to find all current hardcoded args.
            // Use "args" option above to add, this option to remove or manipulate.
            // Using regex: Again, any literal "$" must be escaped to "\\$" to
            // distinguish it from the variable expansion "${...}". Accepted args:
            // [search, [replace, [index, count, new position]]], where:
            // - search:   @type:str (regex)
            // - replace:  @type:str
            // - index:    @type:int (the number is known as a list index); required!
            // - count:    @type:int (the matching occurrences per index, 0 = all); required!
            // - position: @type:int (move old index pos. to new/old one, -1 = delete index); required!'''),
                    ('fix_commands', [
                        NoIndent(['--autocorrect', '--autocorrect-all', 4, 0, 4]),
                        NoIndent(['^.*?auto.*\\$', '--with', 4, 1, 5]),
                        NoIndent(['${packages}/to/old', '${packages}/to/new', 3, 0, 3]),
                        NoIndent(['css', 5, 0, 7]),
                        NoIndent([3, 0, 4]),
                        NoIndent([2, 0, -1]),
                        NoIndent(['--show-tits', 'xxx', 2, 0, -1])
                    ])
                ]))
            ]))
        ])

    beautifiers, minifiers, converters, custom = build_formatter_sublime_settings_children(formatter_map)
    categories = [beautifiers, minifiers, converters, custom]
    for category in categories:
        sorted_category = sorted(category, key=lambda x: list(x.keys())[0])
        for x in sorted_category:
            sublime_settings['formatters'].update(x)

    json_text = json.dumps(sublime_settings, cls=NoIndentEncoder, ensure_ascii=False, indent=4)

    pattern_comment_and_commas = re.compile(r'"__COMMENT__.+"[\s\t]*:[\s\t]*"(.+)",?|[^:]//[^\n]+')
    pattern_comment_linebreaks = re.compile(r'^(.*?//.*)$', re.MULTILINE)
    pattern_comma_before_comment = re.compile(r',([\s\n]+)(/\*)')
    json_text = pattern_comment_and_commas.sub(r'\1', json_text)
    json_text = pattern_comma_before_comment.sub(r'\1\2', json_text)
    matched_lines = pattern_comment_linebreaks.findall(json_text)
    for line in matched_lines:
        modified_line = line.replace(r'\"', '"').replace('\\n', '\n')
        json_text = json_text.replace(line, modified_line)

    s = [
        r'["--autocorrect", "--autocorrect-all", 4, 0, 4],',
        r'["^.*?auto.*\\$", "--with", 4, 1, 5],',
        r'["${packages}/to/old", "${packages}/to/new", 3, 0, 3],',
        r'["css", 5, 0, 7],',
        r'[3, 0, 4],',
        r'[2, 0, -1],',
        r'["--show-tits", "xxx", 2, 0, -1]'
    ]
    r = [
        r'["--autocorrect", "--autocorrect-all", 4, 0, 4], // no index pos change',
        r'["^.*?auto.*\\$", "--with", 4, 1, 5], // using escaped "\\$" regex, move index 4 to pos 5',
        r'["${packages}/to/old", "${packages}/to/new", 3, 0, 3], // variable expansion, no escaped "$"',
        r'["css", 5, 0, 7], // replace the value in index 5 with "css", move it to pos 7',
        r'[3, 0, 4], // just move index 3 to the new pos 4. (count 0 irrelevant)',
        r'[2, 0, -1], // just delete the index 2. (count 0 irrelevant)',
        r'["--show-tits", "xxx", 2, 0, -1] // enough tits, pop it out. ("xxx", 2, 0 irrelevant)'
    ]
    for s, r in zip(s, r):
        json_text = json_text.replace(s, r)

    return strip_trailing(json_text)

def create_package_config_files():
    directory = common.join(sublime.packages_path(), common.PACKAGE_NAME)

    try:
        common.os.makedirs(directory, exist_ok=True)
    except OSError as e:
        if e.errno != os.errno.EEXIST:
            log.error('Could not create directory: %s', directory)
        return False

    file_functions = {
        'Context.sublime-menu': build_context_sublime_menu,
        'Main.sublime-menu': build_main_sublime_menu,
        'Formatter.sublime-commands': build_formatter_sublime_commands,
        'Example.sublime-keymap': build_example_sublime_keymap,
        'Formatter.sublime-settings': build_formatter_sublime_settings
    }

    api = common.Base()

    for file_name, build_function in file_functions.items():
        try:
            text = build_function(formatter_map)
            file = common.join(directory, file_name)
            if common.isfile(file):
                hash_src = common.hashlib.md5(text.encode('utf-8')).hexdigest()
                hash_dst = api.md5f(file)
                if hash_src == hash_dst:
                    continue

            with open(file, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            log.error('An error occurred while saving %s: %s', file, e)
            return False

    try:
        for file in [common.join(directory, common.QUICK_OPTIONS_SETTING_FILE), api.quick_options_config_file()]:
            if not common.isfile(file):
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log.error('An error occurred while saving %s: %s', file, e)
        return False

    return True
