# Arista's EOS SDK RPC protofiles

This repository holds protofiles and documentation for EOS SDK RPC.

A website with full documentation is hosted at: https://aristanetworks.github.io/eossdkrpc.

## Previewing the documentation website

The documentation website can be built and run locally to preview new changes.

```sh
# create and enter a python virtual environment
$ python3 -m venv .venv
$ source .venv/bin/activate

# install dependencies
$ pip install -r requirements.txt

# run the website locally and open the preview link in a browser
$ mkdocs serve
[...]
INFO     -  [04:20:07] Serving on http://127.0.0.1:8000/
[...]
```

By default, the former does not include the API reference (only guides, FAQ, and general structure/look).


## License

All examples and demos available in this repository are provided under [Apache License](LICENSE)
