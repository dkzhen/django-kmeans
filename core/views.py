from itertools import combinations
import io
from io import BytesIO
import base64
import plotly.graph_objects as go
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import os
import matplotlib.pyplot as plt
from django.shortcuts import render, redirect
import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')


# Create your views here.
def preprocessing(request):
    # request.session.clear()
    if bool(request.FILES.get('document', False)) == True:
        uploaded_file = request.FILES['document']
        name = uploaded_file.name
        request.session['name'] = name
        df = pd.read_csv(uploaded_file)
        dataFrame = df.to_json()
        request.session['df'] = dataFrame

        rows = len(df.index)
        request.session['rows'] = rows
        header = df.axes[1].values.tolist()
        request.session['header'] = header

        attributes = len(header)
        types = []
        maxs = []
        mins = []
        means = []
        # statistic attribut
        for i in range(len(header)):
            types.append(df[header[i]].dtypes)
            if df[header[i]].dtypes != 'object':
                maxs.append(df[header[i]].max())
                mins.append(df[header[i]].min())
                means.append(round(df[header[i]].mean(), 2))
            else:
                maxs.append(0)
                mins.append(0)
                means.append(0)

        zipped_data = zip(header, types, maxs, mins, means)
        print(maxs)
        datas = df.values.tolist()
        data = {
            "header": header,
            "headers": json.dumps(header),
            "name": name,
            "attributes": attributes,
            "rows": rows,
            "zipped_data": zipped_data,
            'df': datas,
            "type": types,
            "maxs": maxs,
            "mins": mins,
            "means": means,
        }
    else:
        name = 'None'
        attributes = 'None'
        rows = 'None'
        data = {
            "name": name,
            "attributes": attributes,
            "rows": rows,
        }
    return render(request, 'index.html', data)


def checker_page(request):
    if request.POST:
        drop_header = request.POST.getlist('drop_header')
        print(drop_header)
        for head in drop_header:
            print(head)
        request.session['drop'] = drop_header
        method = request.POST.get('selected_method')
        if method == '2':
            return redirect('clustering')
        else:
            return redirect('preprocessing')
    else:
        return render(request, 'index.html')


def custom_normalization(data):
    max_value = data.max()
    min_value = data.min()
    if max_value == min_value:
        # Handle data with all the same values (e.g., all 0)
        return data
    normalized_data = (data - min_value) / (max_value - min_value)
    return normalized_data


def clustering(request):
    rows = request.session['rows']
    name = request.session['name']
    df = request.session['df']
    df = pd.read_json(df)
    print(df)
    features = request.session['drop']
    print(features)
    nilai_x = features[0]
    nilai_y = features[1]

    feature_data = []


# Loop melalui fitur yang dimasukkan
    for feature in features:
        feature_values = df[feature].values.tolist()
        feature_data.append({
            'feature_name': feature,
            "data": feature_values

        })


# Variabel `feature_data` sekarang berisi array dari data setiap fitur

    if request.method == 'POST' and 'nilai_k' in request.POST:
        k = request.POST['nilai_k']
        nilai_k = int(k)

        x_array = np.array(df.iloc[:, 3:5])

        x_normalized = custom_normalization(x_array)

        scaler = StandardScaler()
        x_scaled = scaler.fit_transform(x_normalized)

        # Menentukan dan mengkonfigurasi fungsi kmeans
        kmeans = KMeans(n_clusters=nilai_k)
        # Menentukan kluster dari data
        kmeans.fit(x_scaled)

        # Calculate cluster centroids
        centers = kmeans.cluster_centers_

        # Menambahkan kolom "kluster" dalam data frame
        df['cluster'] = kmeans.labels_
        cluster = df['cluster'].value_counts()
        clusters = cluster.to_dict()
        sort_cluster = []
        label = []
        for i in sorted(clusters):
            sort_cluster.append(clusters[i])
            label.append(i)

        # Inisialisasi array objek untuk menyimpan data setiap baris
        feature_data.append({
            'feature_name': 'Cluster',
            'data': df['cluster'].values.tolist()
        })
    # Create a scatter plot for each cluster and feature combination
        cluster_combinations = []
        feature_combinations = list(combinations(features, 2))

        for cluster_id in range(nilai_k):
            for feature_x, feature_y in feature_combinations:
                plt.figure()
                cluster_data = df[df['cluster'] == cluster_id]
                plt.scatter(cluster_data[feature_x],
                            cluster_data[feature_y], s=50)
                plt.title(
                    f'Cluster {cluster_id}, Features: {feature_x} and {feature_y}')
                plt.xlabel(feature_x)
                plt.ylabel(feature_y)

                buffer = io.BytesIO()
                plt.savefig(buffer, format="png")
                plt.close()  # Close the plot to release resources

                # Encode the image data to base64
                img_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

                # Append the data URI to the list of cluster plots
                cluster_combinations.append(
                    f"data:image/png;base64,{img_data}")

        if len(features) > 2:
            # Create a 3D scatter plot
            fig = px.scatter_3d(
                df, x=features[0], y=features[1], z=features[2], color=df['cluster'])
            fig.update_layout(scene=dict(xaxis_title=nilai_x,
                              yaxis_title=nilai_y, zaxis_title=features[2]))
        else:
            # Create a 2D scatter plot
            fig = px.scatter(df, x=features[0],
                             y=features[1], color=df['cluster'])

        # Add centroids
        fig.add_trace(go.Scatter(
            x=centers[:, 1], y=centers[:, 0], mode='markers', marker=dict(size=8, color='red')))

        # Update plot title and axis labels
        fig.update_layout(title="Clustering K-Means Results")
        fig.update_xaxes(title_text=nilai_x)
        fig.update_yaxes(title_text=nilai_y)

        # Convert the Plotly figure to HTML
        graph = fig.to_html()
        df_selected = df.loc[:, features]

    # Buat DataFrame baru untuk kolom 'Cluster' dari kolom 'cluster' yang sudah ada
        df_cluster = pd.DataFrame({'Cluster': df['cluster']})

    # Gabungkan df_selected dan df_cluster
        df_combined = pd.concat([df_selected, df_cluster], axis=1)
        df_combined_json = df_combined.values.tolist()

        # print(df_combined_json)
    # print(feature_data)

        if name:
            data = {
                "name": name,
                "clusters": sort_cluster,
                "rows": rows,
                "features": features,
                "label": label,
                "chart": graph,
                "cluster_combinations": cluster_combinations,
                "results": feature_data,
                "data_json": df_combined_json
            }
        else:
            data = {
                "name": '',
            }
    else:
        data = {
            "name": '',
        }

    return render(request, 'clustering.html', data)
