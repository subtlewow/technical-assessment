from flask import Flask, request, jsonify
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import os

app = Flask(__name__)

directory = './staticFiles/' # feel free to change this

if not os.path.exists(directory):
    os.makedirs(directory)

# uploads data / csv
@app.route('/data/<flight_id>', methods=['PUT'])
def put_upload_data(flight_id):
    # non file upload
    if 'file' not in request.files:
        return jsonify({'error': 'File upload only allowed.'}), 400
    
    # restrict length
    if len(flight_id) > 40:
        return jsonify({'error': 'flight-id too long'}), 400
    
    # get uploaded file
    file = request.files['file']
    # empty file
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400
    else:
        path = os.path.join(directory, flight_id + '.csv')
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        file.save(path)
        df = clean_data(path)
        df.to_csv(path, index=False)

    return jsonify({'status': 'success', 'message': 'File uploaded successfully'}), 200

# gets a specific report
@app.route('/report/<flight_id>', methods=['GET'])
def get_report(flight_id):
    filename = os.path.join(directory, flight_id + '.csv')
    
    if not os.path.exists(filename):
        return jsonify({'error': 'Report not found or not yet ready'}), 404
    else:
        df = pd.read_csv(filename, index_col=None)
        summary_report = generate_summary_charts(df, flight_id) # generates pdf report
        
        return jsonify({'summary': summary_report.to_dict()}), 200

# gets all reports
@app.route('/report', methods=['GET'])
def get_all_reports():
    path_dir = os.path.join(directory, 'reports')
    available_reports = []
    
    for file in os.listdir(path_dir):
        if file.endswith('.pdf'):
            # report_id = file[:-4]
            available_reports.append(file)
    
    return jsonify(available_reports), 200

def clean_data(filename):
    df = pd.read_csv(filename, index_col=0)
    
    # removing duplicate datapoints and impute missing data pts
    # method for impute: remove missing data rows (small amount of data missing ~5.5% of all data missing)
    df = df.drop_duplicates(subset=['S1_TC_BC_Ambient.temperature', 
                            'S1_TC_Drip_Tray.temperature', 
                            'S1_TC_HS_AL_Plate.temperature',
                            'S1_TC_HS_E2_9.temperature',
                            'S1_TC_LOx_Tank.temperature']).dropna()
    return df

def generate_summary_charts(df, flight_id):
    summary = df.describe()
    
    pdf_dir = os.path.join(directory, 'reports')
    
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
    
    pdf_path = os.path.join(pdf_dir, f"{flight_id}.pdf")
    combined_fig, combined_ax = plt.subplots(figsize=(10, 10)) # for the final figure combined graphs

    with PdfPages(pdf_path) as pdf:
        for channel in df.columns:
            if channel != 'missionTime':
                fig, _ = plt.subplots(figsize=(10, 10))
                plt.plot(df['missionTime'], df[channel])
                plt.title(f"{channel} over missionTime")
                plt.xlabel('missionTime')
                plt.ylabel(channel)

                roc = rate_of_change(df, col=channel) # y2-y1 / x2-x1
                exceed_pts = df['missionTime'][roc > 5]

                # annotating 'exceedance' pts on graph
                for pt in exceed_pts:
                    plt.scatter(pt, df[channel].loc[df['missionTime'] == pt], color='red')
                    plt.annotate('Exceedance', (pt, df[channel].loc[df['missionTime'] == pt]), fontsize=9)

                pdf.savefig(fig)  # saves to pdf
                plt.close(fig)

                combined_ax.plot(df['missionTime'], df[channel], label=channel)
                
                # plot exceedance on total graph
                for pt in exceed_pts:
                    combined_ax.scatter(pt, df[channel].loc[df['missionTime'] == pt], color='red')

        combined_ax.legend(loc='upper right')
        combined_ax.set_title('All Channels over missionTime')
        combined_ax.set_xlabel('missionTime')

        pdf.savefig(combined_fig) 
        plt.close(combined_fig)
                
    return summary

# function is for testing in test_main.py
def rate_of_change(data, col):
    return data[col].diff() / data['missionTime'].diff()

if __name__ == '__main__':
    app.run()
