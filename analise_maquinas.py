from time import time
import pandas as pd
import os, re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
from scipy.signal import welch
import numpy as np

#Função para ler mais de um arquivo de cada vez
def file_reader(*args, **kwargs):
    filetype = kwargs.get('filetype', None)
    columns = kwargs.get('columns', None)
    sep = kwargs.get('sep', ',')
    try:
        if filetype == None:
            if args[0].__class__ == list:
                return [pd.read_csv(x, names=columns, sep=sep) for x in args[0]]
            else:
                return [pd.read_csv(x, names=columns, sep=sep) for x in args]
        elif filetype == 'xlsx' | filetype == 'excel':
            if args[0].__class__ == list:
                return [pd.read_excel(x, names=columns, sep=sep) for x in args[0]]
            else:
                return [pd.read_excel(x, names=columns, sep=sep) for x in args]
    except UnicodeDecodeError:
        if filetype == None:
            if args[0].__class__ == list:
                return [pd.read_csv(x, names=columns, sep=sep, encoding='ISO-8859-1') for x in args[0]]
            else:
                return [pd.read_csv(x, names=columns, sep=sep, encoding='ISO-8859-1') for x in args]
        elif filetype == 'xlsx' | filetype == 'excel':
            if args[0].__class__ == list:
                return [pd.read_excel(x, names=columns, sep=sep, encoding='ISO-8859-1') for x in args[0]]
            else:
                return [pd.read_excel(x, names=columns, sep=sep, encoding='ISO-8859-1') for x in args]

def main():
    #Configuração dos gráficos
    plt.style.use('ggplot')
    plt.rcParams['figure.figsize'] = 12,9

    #Ler arquivos e transformá-los em DataFrames
    path = 'D:\Binahki\Dados de Vibração e Temperatura'
    filenames = [(path + '\\' + file) for file in os.listdir(path)]
    df_list = file_reader(filenames, columns=['accX', 'accY', 'accZ', 'temp']) #Função que lê todos os arquivos e os coloca em uma lista

    #Para encontrar tempo inicial e tempo final de cada DataFrame
    p = re.compile(r' - ')
    inicio = []
    fim = []
    for file in filenames:
        result = p.search(file)
        s = result.span()
        inicio.append(file[s[0]-10:s[0]])
        fim.append(file[s[1]:-4])
    
    #Colocando horários em formato apropriado
    inicio_t = [datetime.fromtimestamp(int(i)) for i in inicio]
    fim_t = [datetime.fromtimestamp(int(i)) for i in fim]

    del inicio, fim #Deletando objetos que nao serão mais utilizados
    
    N = [len(i.index) for i in df_list] #Nº de medidas de cada DataFrame
    tempo_total = [(fim_t[i]-inicio_t[i]).total_seconds() for i in range(len(df_list))] #Tempo total de cada DataFrame
    timestep = [float(f'{N[i]/tempo_total[i]:.3f}') for i in range(len(df_list))] #período de cada DataFrame

    #Cada coluna das DataFrames como numpy arrays
    arrx = [np.asanyarray(i['accX']) for i in df_list]
    arry = [np.asanyarray(i['accY']) for i in df_list]
    arrz = [np.asanyarray(i['accZ']) for i in df_list]
    temp = [np.asanyarray(i['temp']) for i in df_list]
    
    #Periodograma de cada direção
    fx, fy, fz = [], [], []
    for i in range(len(df_list)):
        f1, Pxx_Derx = welch(arrx[i], timestep[i])
        f2, Pxx_Dery = welch(arry[i], timestep[i])
        f3, Pxx_Derz = welch(arrz[i], timestep[i])

        #Eixo x
        fx.append((f1[1:],Pxx_Derx[1:]))
        #Eixo y
        fy.append((f2[1:],Pxx_Dery[1:]))
        #Eixo z
        fz.append((f3[1:],Pxx_Derz[1:]))

    #Gráfico das temperaturas 
    all_dfs = pd.concat(df_list, ignore_index=True)
    cutoffs = []
    cut_sum = -1
    for i in df_list:
        cut_sum += len(i.index)
        cutoffs.append(cut_sum)
    temp = all_dfs.iloc[:,-1].rolling(window=30).mean()
    plt.plot(np.asanyarray(temp))
    plt.ylabel('Temperatura')
    plt.title('Temperatura (média 30 medidas)')
    [plt.axvline(cutoff, color='k', ls='--') for cutoff in cutoffs] 
    #plt.show()

    #Gráfico das potências de cada eixo pela frequência
    for name, axis in {'X' : fx, 'Y' : fy, 'Z' : fz}.items():
        for x in range(len(df_list)):
            plt.semilogy(axis[x][0], axis[x][1])
        plt.title(f'PSD Eixo {name}')
        plt.xlabel('frequência [Hz]')
        plt.ylabel('Power')
        plt.xlim([0.0, 100])
        #plt.show()

    #Cálculo do downtime/uptime (considerando padrões encontrados nos sinais de vibração)
    downtime = 0
    uptime = 0
    for i in range(len(df_list)):
        #Condição para estar ligado
        if df_list[i]['accX'].describe().loc['std'] > 1.0e-01 and df_list[i]['accY'].describe().loc['std'] > 1.0e-01 and df_list[i]['accZ'].describe().loc['std'] > 1.0e-01:
            uptime += tempo_total[i]
        #Condição para estar desligado (ter um desvio padrão menor que 0.1)
        else:
            downtime += tempo_total[i]
    
    #Cálculo do tempo ligado/desligado em minutos
    uptime = divmod(uptime, 60)
    downtime = divmod(downtime, 60)
    print(f'Tempo Ligado : {int(uptime[0])} minutos e {int(uptime[1])} segundos')
    print(f'Tempo Desligado : {int(downtime[0])} minutos e {int(downtime[1])} segundos')
    

if __name__ == '__main__':
    main()
