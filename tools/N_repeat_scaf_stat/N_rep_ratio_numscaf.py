"""
输入文件：
目标文件 tab [id start end]
N 区域 Npos [id start end]
重复序列区域 repeat pos [id start end]
scaffold position 文件 [chrid start end scafid]
除目标文件外，其他三个文件均可选，但不能同时缺失。

对输入文件以指定列（id 和 start）进行去 overlap，排序。
统计目标文件每一行 (start to end) N 的比例，重复序列比例，以及 scafffold 条数
输出格式：
id start end Nratio rep scaffoldcount
"""

import pandas as pd
import argparse
import sys

import remove_overlap

import warnings

warnings.simplefilter(action='ignore')


class Line(object):
    def __init__(self, line):
        self.line = line.values

    @property
    def start(self):
        return int(self.line[1])

    @property
    def end(self):
        return int(self.line[2])

    @property
    def id(self):
        return self.line[0]

    @property
    def scaf(self):
        return self.line[3] if len(self.line) == 4 else '1'

    def __str__(self):
        return '\t'.join((self.id, str(self.start), str(self.end), self.scaf))


class TableFile(object):
    def __init__(self, table, filetype='table'):
        self.table = table
        self.filetype = filetype
        self.df = self.table_to_df()

    def table_to_df(self):
        if self.filetype == 'table':
            try:
                df = pd.read_csv(self.table, sep='\s+', comment='#', header=None, names=['id', 'start', 'end'])
                return df
            except:
                return None
        elif self.filetype == 'agp':
            try:
                df = pd.read_csv(self.table, sep='\s+', comment='#', header=None, names=['id', 'start', 'end', 'scaf'])
                return df
            except:
                return None

    def in_range(self, row, tstart, tend):
        return [row['start'] >= tstart and row['end'] <= tend,
                row['start'] <= tstart <= row['end'],
                row['start'] <= tend <= row['end']]

    def check_df(self, df_flag, tstart, tend):
        df, flag = df_flag
        if flag == 'all':
            return df
        elif flag == 'before':
            if len(df) > 0:
                assert len(df) == 1
                df['start'] = [tstart]
            return df
        elif flag == 'after':
            if len(df) > 0:
                assert len(df) == 1
                df['end'] = [tend]
            return df

    def parse_table(self, target_line):
        tid, tstart, tend, scaf = target_line.id, target_line.start, target_line.end, target_line.scaf
        df = self.df[self.df['id'] == tid]
        df_condition = pd.DataFrame(df.apply(lambda r: self.in_range(r, tstart, tend), axis=1).values.tolist(),
                                    columns=['all', 'before', 'after'])
        cols = df_condition.columns
        dfs = [df[list(df_condition[i])] for i in cols]
        df_all, df_before, df_after = [self.check_df(df_flag, tstart, tend) for df_flag in zip(dfs, cols)]
        df = pd.concat((df_all, df_before, df_after))
        return df

    def table_prop(self, target_line):
        tid, tstart, tend = target_line.id, target_line.start, target_line.end
        df = self.parse_table(target_line)
        try:
            total = (df['end'] - df['start']).sum() if len(df) > 0 else 0
            prop = total / (tend - tstart)
        except KeyError:
            prop = 0
        return prop

    def print_scaf(self, target_line, unique_scaf):
        for i in unique_scaf:
            print(target_line, end='\t', file=sys.stderr)
            print(len(unique_scaf), end='\t', file=sys.stderr)
            print(i, file=sys.stderr, flush=True)

    def table_count(self, target_line):
        df = self.parse_table(target_line)
        try:
            cnt = len(df['scaf'].unique())
            if len(df['scaf'].unique()) > 0:
                self.print_scaf(target_line, df['scaf'].unique())
        except KeyError:
            cnt = 0
        return cnt

    def __iter__(self):
        df = self.df.sort_values(by=['id', 'start'])
        for index, row in df.iterrows():
            yield Line(row)


class TargetFile(TableFile):
    def __init__(self, targetfile):
        super(TargetFile, self).__init__(targetfile)

    def table_to_df(self):
        try:
            df = pd.read_csv(self.table, sep='\s+', comment='#', header=None, names=['id', 'start', 'end'])
            df.sort_values(by=['id', 'start'], inplace=True)
            return df
        except:
            return None


class StatInfo(object):
    def __init__(self, target, npos='', repeat='', agp=''):
        self.target = target
        self.npos = npos
        self.repeat = repeat
        self.agp = agp
        self.check_file(self.npos, self.repeat, self.agp)

    def check_file(self, npos, repeat, agp):
        if not (npos or repeat or agp):
            raise ValueError('you should input at least one file in [npos, repeatfile, agp]')

    def stat(self):
        target = TargetFile(self.target)
        targetdf = target.table_to_df()
        repeat_table = TableFile(self.repeat)
        npos_table = TableFile(self.npos)
        agp_table = TableFile(self.agp, filetype='agp')
        reap_prop, n_prop, scaf_cnt = [], [], []
        for l in target:
            if self.repeat:
                reap_prop.append(repeat_table.table_prop(l))
            if self.npos:
                n_prop.append(npos_table.table_prop(l))
            if self.agp:
                scaf_cnt.append(agp_table.table_count(l))
        for i, ls in zip(('repeat_prop', 'n_prop', 'scaf_count'), [reap_prop, n_prop, scaf_cnt]):
            if ls:
                targetdf[i] = ls
        suffix = '_'.join(i.split('_')[0] for i in targetdf.columns[3:])
        targetdf.to_csv(f'output_{suffix}.csv', sep='\t', index=False)


def arguements():
    parser = argparse.ArgumentParser(
        description='Statistics target line infomation about repeat seq proportion, n ratio, scaffold number',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-t', "--target", help="the target file. [id start end]", required=True)
    parser.add_argument("-r", "--repeat", help="repeat annotation file. [id start end]")
    parser.add_argument("-n", "--npos", help="n pos file. [id start end]")
    parser.add_argument("-g", "--scaf", help="chr and scaffold agp file. [chr start end scaffold]")

    args = parser.parse_args()
    return args


def main():
    args = arguements()
    target, repeat, npos, agp_tab = args.target, args.repeat, args.npos, args.scaf
    de_overlap = lambda x: remove_overlap.main(x) if x else None
    repeat, npos, agp_tab = map(de_overlap, [repeat, npos, agp_tab])
    si = StatInfo(target, repeat=repeat, npos=npos, agp=agp_tab)
    si.stat()


if __name__ == '__main__':
    main()
