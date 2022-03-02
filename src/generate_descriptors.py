import logging
from typing import Optional

import numpy as np
import pandas as pd
import typer
from click._termui_impl import ProgressBar
from descriptastorus.descriptors import rdNormalizedDescriptors
from rdkit import Chem

cli = typer.Typer()

generator = rdNormalizedDescriptors.RDKit2DNormalized()
feature_columns = generator.columns


def rdkit_2d_normalized_features(smiles: str, progressbar: Optional[ProgressBar] = None):
    # convert smiles to canonical smiles
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return
    smiles = Chem.MolToSmiles(mol)
    # n.b. the first element is true/false if the descriptors were properly computed
    results = generator.process(smiles)
    processed, features = results[0], results[1:]
    if not processed:
        logging.warning("Unable to process smiles %s", smiles)
        return
    # if processed is None, the features are are default values for the type
    if progressbar is not None:
        progressbar.update(n_steps=1)
    return features


@cli.command()
def generate_features(input_file: str, output_file: str, frac: Optional[float] = None) -> None:
    input_data = pd.read_csv(input_file)
    if frac is not None:
        input_data = input_data.sample(frac=frac)
    progressbar: ProgressBar = typer.progressbar(length=len(input_data))
    feature_data = input_data["smiles"].apply(lambda smiles: rdkit_2d_normalized_features(smiles, progressbar))
    feature_data = feature_data.dropna()
    feature_data = np.stack(feature_data.values)  # convert from series of lists into single 2d np array
    np.savetxt(output_file, feature_data, delimiter=",")


if __name__ == "__main__":
    cli()
