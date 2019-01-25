# N_rep_ratio_numscaf.py

根据目标文件 `-t` 的目标区域，统计 N 和重复序列的比例以及根据 agp 文件统计目标区域内的 scaffold 条数。

输入文件：

`-t` [id start end]

`-r` [id start end]

`-n` [id start end]

`-g` [id start end scafid]

```python
python N_rep_ratio_numscaf.py -t data/test.txt -r data/ncbi.repeat -n data/ncbi.n.tab -g data/test.agptab
```

`-r` | `-n` |  `-g` 至少需要一个。

# remove_overlap.py

输入文件：

`-i` tab 文件，分隔符由 `-s` 指定

`-c` 指定 column id

`python remove_overlap.py -i data/test.txt -c 0 1 2`

