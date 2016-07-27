from rio_toa.toa_utils import _load_mtl

import os, shutil

allf = os.listdir('/tmp/mtlsamples')

jsonmtls = {f.split('.')[0]: f for f in allf if f.split('.')[-1] == 'json'}

txtmtls = {f.split('.')[0]: f for f in allf if f.split('.')[-1] == 'txt'}

for k in jsonmtls.keys():
    if k in txtmtls:
        txt_mtl, json_mtl = (_load_mtl(os.path.join('/tmp/mtlsamples', txtmtls[k])), _load_mtl(os.path.join('/tmp/mtlsamples', jsonmtls[k])))
        if not txt_mtl == json_mtl:
            for sk in json_mtl["L1_METADATA_FILE"].keys():
                print sk
                print sorted(json_mtl["L1_METADATA_FILE"][sk].keys())
                print sorted(txt_mtl["L1_METADATA_FILE"][sk].keys())
            
            # shutil.copy(os.path.join('/tmp/mtlsamples', txtmtls[k]),
            #     os.path.join('/tmp/badmtls', txtmtls[k]))
            # shutil.copy(os.path.join('/tmp/mtlsamples', jsonmtls[k]),
            #     os.path.join('/tmp/badmtls', jsonmtls[k]))
