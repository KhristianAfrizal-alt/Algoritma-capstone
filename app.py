from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

app = Flask(__name__)

playstore = pd.read_csv('data/googleplaystore.csv')

playstore.drop_duplicates(subset =["App"], keep="first", inplace=True) 

# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore = playstore.drop([10472])

playstore['Category'] = playstore.Category.astype("category")
# Buang tanda koma(,) dan tambah(+) kemudian ubah tipe data menjadi integer
playstore['Installs'] = playstore.Installs.apply(lambda x: x.replace(",",""))
playstore['Installs'] = playstore.Installs.apply(lambda x: x.replace("+",""))

# Bagian ini untuk merapikan kolom Size, Anda tidak perlu mengubah apapun di bagian ini
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

playstore['Price'] = playstore['Price'].apply(lambda x: x.replace('$', ''))
playstore['Price'] = playstore['Price'].astype('float64')

# Ubah tipe data Reviews, Size, Installs ke dalam tipe data integer
list_int = ['Reviews', 'Size', 'Installs']
playstore[list_int] = playstore[list_int].astype('int64')

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore.copy()

    # Statistik
    top_category = pd.crosstab(
    index = df2['Category'],
    columns = 'Jumlah'
    ).sort_values(by = 'Jumlah', ascending = False).reset_index()
    # Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        'most_categories' : top_category['Category'][0],
        'total': top_category['Jumlah'][0],
        'rev_table' : df2.groupby(['Category', 'App']).agg({
        'Reviews' : 'sum', 
        'Rating' : 'mean'
        }).sort_values('Reviews', ascending = False).head(10).reset_index().to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    ## Bar Plot
    cat_order = df2.groupby(['Category']).agg({
        'App' : 'count'
        }).rename({'Category':'Total'}, axis=1).sort_values('App', ascending = False).head()
    X = cat_order.reset_index()['Category']
    Y = cat_order.reset_index()['App']
    my_colors = ['r','g','b','k','y','m','c']
    # bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    # bagian ini digunakan untuk membuat bar plot
    plt.barh(X, Y, color=my_colors)
    # bagian ini digunakan untuk menyimpan plot dalam format image.png
    plt.savefig('cat_order.png',bbox_inches="tight") 

     # bagian ini digunakan untuk mengconvert matplotlib png ke base64 agar dapat ditampilkan ke template html
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    # variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
    # halaman html
    result = str(figdata_png)[2:-1]
    
    ## Scatter Plot
    X = df2['Reviews'].values # axis x
    Y = df2['Rating'].values # axis y
    area = playstore['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    # isi nama method untuk scatter plot, variabel x, dan variabel y
    plt.scatter(x=X, y=Y, s=area, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('rev_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    ## Histogram Size Distribution
    X=(playstore['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    ## Buatlah sebuah plot yang menampilkan insight di dalam data 

    # Data apps playstore type Free saja
    list_apps_free = playstore[(playstore['Type'] == 'Free')]

    # Frekuensi applikasi setiap kategori khusus Apps type Free saja
    top_category_free = pd.crosstab(
        index = list_apps_free['Category'],
        columns = 'Jumlah Frekuensi'
    ).sort_values(by = 'Jumlah Frekuensi', ascending = False)

    # Data apps playstore type Paid saja
    list_apps_paid = playstore[(playstore['Type'] == 'Paid')]

    # Frekuensi applikasi setiap kategori khusus Apps type Paid saja
    top_category_paid = pd.crosstab(
        index = list_apps_paid['Category'],
        columns = 'Jumlah Frekuensi'
    ).sort_values(by = 'Jumlah Frekuensi', ascending = False)

    X1 = top_category_free.head(5).reset_index()['Category']
    Y1 = top_category_free.head(5).reset_index()['Jumlah Frekuensi']

    X2 = top_category_paid.head(5).reset_index()['Category']
    Y2 = top_category_paid.head(5).reset_index()['Jumlah Frekuensi']

    # Stacking subplots vertically
    fig = plt.figure(figsize=(8,10),dpi=600)
    fig, axs = plt.subplots(2)
    fig.suptitle('Top 5 Most Frequent Category', fontsize=16)

    axs[0].barh(X1, Y1, color = 'b')
    # Show top values
    axs[0].invert_yaxis()
    axs[0].set_title('FREE APPS')

    axs[1].barh(X2, Y2, color = 'm')
    # Show top values
    axs[1].invert_yaxis()
    # Add Plot Title
    axs[1].set_title('PAID APPS')

    for ax in axs.flat:
        ax.set(xlabel='Jumlah Frekuensi', ylabel='Category')
    
    fig.tight_layout()
    plt.savefig('top_5_freq_cat_free_vs_paid.png')
    
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1]

    # Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3)

if __name__ == "__main__": 
    app.run(debug=True)
