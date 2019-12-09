import pandas as pd 
import json
from tqdm import tqdm 
from geopy.distance import geodesic
import wget
import sys, os
import click


@click.command()
@click.option("--url", prompt="url", help="python3 ysc-distance.py --url='https://sdcimages.s3.yandex.net/test_task/data'")
def calculate(url):
    click.echo('downloading:')
    try:
        os.remove(url.rsplit('/', 1)[-1])
    except: pass
    filename = wget.download(url)

    click.echo('\ndata processing:')
    with open(f'{filename}', 'r') as f:
        data = f.readlines()
    data = [json.loads(x) for x in data]
    data = sorted(data, key=lambda k: k['ts'])

    controls = [x for x in data if 'control_switch_on' in x.keys()]
    points = [x for x in data if 'control_switch_on' not in x.keys()]
    
    # определение позиции control_switch для точек маршрута
    df_controls = pd.DataFrame(controls)
    for x in tqdm(range(len(points))):
        if points[x]['ts'] >= min(df_controls.ts.to_list()):
            if df_controls.loc[(df_controls['ts'] <= points[x]['ts']).idxmin(), 'control_switch_on'] == True:
                points[x]['autopilot'] = True
            else:
                points[x]['autopilot'] = False
    df_points = pd.DataFrame(points).dropna()
    pts = df_points.to_dict('records')

    click.echo('distance calculation:')
    selfd = 0
    humand = 0
    tmp_points = []
    for x in tqdm(range(len(pts)-1)):
        tmp_points.append([pts[x]['geo']['lat'], pts[x]['geo']['lon']])
        curpos = pts[x]['autopilot']
        nextpos = pts[x+1]['autopilot']

        # расчёт дистанции по точкам между изменениями позиции переключателя 
        if curpos != nextpos:
            for i in range(len(tmp_points)-1):
                if 0 not in tmp_points[i] and 0 not in tmp_points[i+1]:
                    distance = geodesic(tmp_points[i], tmp_points[i+1]).m
                    if curpos == True:
                        selfd += distance
                    else:
                        humand += distance
                        
            del tmp_points[:]
        
        # для последней точки 
        elif x == len(pts)-1 and curpos == nextpos:
            tmp_points.append([pts[x+1]['geo']['lat'], pts[x+1]['geo']['lon']])
            for i in range(len(tmp_points)-1):
                if 0 not in tmp_points[i] and 0 not in tmp_points[i+1]:
                    distance = geodesic(tmp_points[i], tmp_points[i+1]).m
                    if curpos == True:
                        selfd += distance
                    else:
                        humand += distance
            del tmp_points[:]
    
    click.echo(f'selfdriving: {selfd} m')
    click.echo(f'humandriving: {humand} m')


if __name__ == '__main__':
    try:
        calculate()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        click.echo(f'error at line {exc_tb.tb_lineno}: {e}')
