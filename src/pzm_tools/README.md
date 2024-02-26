#Subcommands: `label`

This command first parses the input VCF file into a pandas DataFrame, 
then labels each variant in the DataFrame using the trained random forest model. 
These steps are explained in details in the following.

## Parse VCF

The parser reads an input VCF into a pandas DataFrame and 
applies mappings to convert variants properties to their numerical or categorical equivalent as necessary, 
optionally normalizes the values and filters variants based on the hard-coded criteria or blacklist regions. 
Specifically, it takes the following steps. 

- **Read raw VCF into pandas DataFrame**:
  - Iterate through every variant in the VCF file, and map their info and genotype fields as needed. 
    See [these lines](https://github.com/talkowski-lab/pzm/blob/c29abd116f0837f67615142763e7a39e267e376e/src/pzm_tools/pzm_tools/modules/parser.py#L38-L137)
    for the applied maps. Each map is defined on a single field, it takes the value of the field
    from the VCF file, and converts it as defined in the map. Please see the following examples.

    - Example 1, `GERMQ`:
    
      ```python
      "GERMQ": Mapper(True, {}, lambda x: {"GERMQ": int(x)}, ["GERMQ"])
      ```
    
      This mapping declares that it is defined for `GERMQ`, and it takes the 
      value given to the field in the VCF file, and converts it to an integer.

    - Example 2, `MBQ`: 

      ```python
      "MBQ": Mapper(True, {}, lambda x: {"MBQ_ref": int(x[0]), "MBQ_alt": int(x[1])}, ["MBQ_ref", "MBQ_alt"]),
      ```
      
      This mapping is defined for `MBQ`. It takes the value given in the input VCF, 
      and returns two integers in the output, `MBQ_ref` and `MBQ_alt`, assigned the 
      first and second values from the VCF representing each allele.

    - Example 3, `RMCL`:
    
      ```python
      "RMCL": Mapper(
        False, 
        {"RMCL": self.get_rmcl_encoding((self.no_repeat_masker_key,))},
        lambda x: {"RMCL": self.get_rmcl_encoding(x)}, 
        ["RMCL"]
      )
      ```
      
      This mapping converts the categorical values given to `RMCL` in the input VCF, 
      to their one-hot encoding equivalent. If `RMCL` is provided for a variant, 
      it returns its one-hot encoding, otherwise, it generates an encoding for the default 
      value for the repeat masker (current set to `"no_repeat_masker"`).
  
    This mapping approach is highly expressive as it enables developing and using custom 
    mapping functions from the value given in the VCF to the value in pandas DataFrame, 
    while it enables converting an input from VCF to multiple features in the dataframe 
    (e.g., the mapping defined for `MBQ`).

  - Generate a unique identifier for each variant as base64 encoding of its discriminative properties
    (i.e., `chr`, `position`, `ref` and `alts`).

- **Normalize DataFrame** [Optional]:

  Normalize every feature (column) in the DataFrame independently using the 
  [MinMaxScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html)
  method. The following features (columns) are excluded from the normalization. 

  - Identifier fields, such as `chrom`, `pos`, or base64 encoding. Please refer to 
    [these lines in the code](https://github.com/talkowski-lab/pzm/blob/c29abd116f0837f67615142763e7a39e267e376e/src/pzm_tools/pzm_tools/modules/parser.py#L232-L234)
    for the most up-to-date list.
  - [genotype fields](https://github.com/talkowski-lab/pzm/blob/c29abd116f0837f67615142763e7a39e267e376e/src/pzm_tools/pzm_tools/modules/parser.py#L108-L137)
    that are not sample metrics. For instance, `AD`, `AF`, and `DP`. Please refer to 
    [these lines of code](https://github.com/talkowski-lab/pzm/blob/c29abd116f0837f67615142763e7a39e267e376e/src/pzm_tools/pzm_tools/modules/parser.py#L108-L137)
    for the most up-to-date list of the fields.
  - Boolean features.


- **Filter DataFrame** [Optional]:

  Variants in the DataFrame are removed based on some hard-coded criteria (e.g., `AF >= 0.3675`)
  and if they overlap with intervals defined a blacklist regions file. Please refer to the 
  [method implementation](https://github.com/talkowski-lab/pzm/blob/c29abd116f0837f67615142763e7a39e267e376e/src/pzm_tools/pzm_tools/modules/parser.py#L252-L296)
  for details on the hard-coded criteria and overlapping with the blacklist regions.


## Labeling

The labeling method, labels each variant in the DataFrame as PZM or not,
leveraging a trained random forest model.
The model is trained using a dataset containing molecularly validated variants as PZM or not.
The latest trained model is available from 
[this directory on GitHub](https://github.com/talkowski-lab/pzm/tree/main/src/test_data).

The method first removes from the DataFrame the columns not used for training and prediction 
(e.g., `chrom` and `pos`, you may refer to 
[these lines of code](https://github.com/talkowski-lab/pzm/blob/c29abd116f0837f67615142763e7a39e267e376e/src/pzm_tools/pzm_tools/modules/filter.py#L20-L21)
for a complete list of dropped columns). 
The method then adds a new column, labeled 
[`y_predict`](https://github.com/talkowski-lab/pzm/blob/c29abd116f0837f67615142763e7a39e267e376e/src/pzm_tools/pzm_tools/modules/filter.py#L9),
to the DataFrame, with values being `PZM` or `Not_PZM`. 
