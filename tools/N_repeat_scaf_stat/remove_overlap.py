"""
先按照 id 和 start 进行排序
再根据 start 和 end 去 overlap
"""
import pandas as pd
import os
import argparse


def sort_file(inputfile, infos, out, sep):
    df = pd.read_csv(inputfile, sep=sep, header=None, comment='#')
    id, start = df.columns[infos[0]], df.columns[infos[1]]
    df.sort_values(by=[id, start], inplace=True)
    df.to_csv(out, sep='\t', index=False, header=None)
    return out


def remove_overlap(sort_table, infos, out, sep=''):
    def new_line(line, infostuple):
        for i, v in infostuple:
            line[i] = v
        return line

    outp = open(out, 'w')
    n, s, e = infos
    faid = ''
    with open(sort_table) as f:
        for l in f:
            line = l.strip().split('\t')
            assert int(line[s]) <= int(line[e])
            # 判断是否是一条新序列
            if faid != line[n]:
                # 写入上一条
                if faid:
                    outp.write('\t'.join(new_line(pre_line, zip(infos, [pre_id, str(mins), str(maxe)]))) + '\n')
                # 新序列需要更新 id, start, end, mins, maxe
                faid, start, end = line[n], int(line[s]), int(line[e])
                mins = min(float('inf'), start)
                maxe = max(0, end)
            else:
                if int(line[s]) > maxe:
                    # 写入上一条信息
                    outp.write('\t'.join(new_line(pre_line, zip(infos, [pre_id, str(mins), str(maxe)]))) + '\n')
                    faid, start, end = line[n], int(line[s]), int(line[e])
                    mins = min(float('inf'), start)
                    maxe = max(0, end)
                mins = min(mins, int(line[s]))
                maxe = max(maxe, int(line[e]))
                pre_line, pre_id = line, faid
            # 某个 id 下只有一行，不做更新
            pre_line, pre_id = line, faid
        outp.write('\t'.join(new_line(line, zip(infos, [faid, str(mins), str(maxe)]))))
    return out


def check_run(func, inputfile, infos, out, sep):
    if os.path.exists(out):
        return out
    else:
        return func(inputfile, infos, out, sep)


def main(inputfile, infos=(0, 1, 2), sep='\s+'):
    out = inputfile + '.sort'
    sort_out = check_run(sort_file, inputfile, infos, out, sep)
    out = inputfile + '.remove_overlap'
    removeout = check_run(remove_overlap, sort_out, infos, out, sep)
    return removeout


def arguements():
    parser = argparse.ArgumentParser(
        description='remove overlap in table file',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-i', "--input", help="the input file", required=True)
    parser.add_argument("-c", "--colid", nargs=3, type=int, required=True,
                        help="the columns number contains 'id start end'."
                             "example: 0 1 2 means the 1st, 2nd and 3rd cols.")
    parser.add_argument('-s', "--seperator", help="the input file seperator", default='\s+')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = arguements()
    main(args.input, args.colid, args.seperator)
