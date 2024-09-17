import os
import json

class Sidecar(dict):
    
    @classmethod
    def from_path(cls, path):
        with open(path, "r") as file:
            dct = json.load(file)

        new_sidecar = cls(dct)
        new_sidecar.bids_name = path.split("/")[-1]
        new_sidecar.path = path

        return new_sidecar

    def write(self, keep_back=True):
        if keep_back:
            os.rename(self.path, self.path + ".bak")

        with open(self.path, "w") as file:
            json.dump(self, file)

        return self.path