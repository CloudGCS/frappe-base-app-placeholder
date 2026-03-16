import json

mock_packet_install = {
    'title': 'Packet 1',
    'code_name': 'packet1',
    'major': '2',
    'minor': '1',
    'service_provider': {
        'name': 'Provider-1',
        'title': 'Provider 1'
    },
    'extensions': [
        {
            'title': 'Extension 1',
            'library_name': 'extension1',
            'major': '1',
            'minor': '3',
            'file_path': 'extension1.zip',
            'extension_type': {
                'name': 'PS',
                'title': 'Pilot Station Pugin'
            },
        },
        {
            'title': 'Extension 2',
            'library_name': 'extension2',
            'major': '2',
            'minor': '0',
            'file_path': 'extension2.zip',
            'extension_type': {
                'name': 'MC',
                'title': 'Mission Controller Plugin'
            },
        }
    ]
}

mock_packets = [
    {'name': 'packet1', 'title': 'Packet 1', 'release_version': '1.0', 'service_provider': 'Provider 1'},
    {'name': 'packet2', 'title': 'Packet 2', 'release_version': '2.0', 'service_provider': 'Provider 2'},
    {'name': 'packet3', 'title': 'Packet 3', 'release_version': '3.0', 'service_provider': 'Provider 3'},
    {'name': 'packet3', 'title': 'Packet 3', 'release_version': '3.1', 'service_provider': 'Provider 3'},
    {'name': 'Deneme-RP', 'title': 'Remote Piloting', 'release_version': 'Deneme-RP-v0.1',
     'service_provider': 'Deneme'},
    {'name': 'Deneme-RP', 'title': 'Remote Piloting', 'release_version': 'Deneme-RP-v2.0',
     'service_provider': 'Deneme'},
    {'name': 'Provider-1-packet1', 'title': 'Packet 1', 'release_version': 'Provider-1-packet1-v2.1',
     'service_provider': 'Provider-1'},
]


def mock_api():
    return json.dumps(mock_packets)


def mock_install_api(x, y):
    return json.dumps(mock_packet_install)
