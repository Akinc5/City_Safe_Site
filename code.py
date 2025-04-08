import pdfplumber
import pandas as pd
import folium
from folium.features import DivIcon
import requests
import time
import os
from flask import Flask, render_template, jsonify, send_from_directory,request

app = Flask(__name__)

# Directory for static files
os.makedirs('static', exist_ok=True)

# Function to get coordinates using Nominatim OpenStreetMap API
def get_coordinates(location_name, state="Telangana", country="India"):
    """Get coordinates for a location using Nominatim OpenStreetMap API"""
    print(f"🔍 Geocoding: {location_name}...", end="", flush=True)
    
    base_url = "https://nominatim.openstreetmap.org/search"
    
    # Append state and country for better results
    query = f"{location_name}, {state}, {country}"
    
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
    }
    
    # Add a user-agent to comply with Nominatim usage policy
    headers = {
        "User-Agent": "TelanganaDistrict_CrimeMap/1.0"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        # If we got results, return the first one's coordinates
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f" ✅ Found: [{lat}, {lon}]")
            return [lat, lon]
        else:
            print(f" ❌ Not found")
            return None
    except Exception as e:
        print(f" ❌ Error: {str(e)[:50]}...")
        return None

def process_crime_data(pdf_path):
    # Hard-coded coordinates for districts in Telangana (2020-2022)
    manual_coords = {
        "Adilabad": [19.6641, 78.5320],
        "Bhadradri Kothagudem": [17.5555, 80.6190],
        "Hyderabad": [17.3850, 78.4867],
        "Jagtial": [18.7947, 78.9138],
        "Jangaon": [17.7250, 79.1520],
        "Jayashankar Bhupalpalli": [18.1973, 79.9383],
        "Jogulamba Gadwal": [16.2342, 77.8062],
        "Kamareddy": [18.3219, 78.3410],
        "Karimnagar": [18.4392, 79.1288],
        "Khammam": [17.2473, 80.1514],
        "Komaram Bheem Asifabad": [19.3647, 79.2798],
        "Mahabubabad": [17.6033, 80.0021],
        "Mahabubnagar": [16.7375, 77.9803],
        "Mancherial": [18.8741, 79.4637],
        "Medak": [18.0453, 78.2608],
        "Medchal-Malkajgiri": [17.5409, 78.4891],
        "Mulugu": [18.1972, 80.1846],
        "Nagarkurnool": [16.4822, 78.3245],
        "Nalgonda": [17.0583, 79.2671],
        "Narayanpet": [16.7452, 77.4954],
        "Nirmal": [19.0965, 78.3441],
        "Nizamabad": [18.6730, 78.1000],
        "Peddapalli": [18.6150, 79.3742],
        "Rajanna Sircilla": [18.3866, 78.8318],
        "Rangareddy": [17.3026, 78.3641],
        "Sangareddy": [17.6291, 78.0938],
        "Siddipet": [18.1019, 78.8521],
        "Suryapet": [17.1449, 79.6339],
        "Vikarabad": [17.3384, 77.9045],
        "Wanaparthy": [16.3679, 77.8121],
        "Warangal": [17.9784, 79.5910],
        "Yadadri Bhuvanagiri": [17.5083, 78.8824],
        "Cyberabad Commissionerate": [17.4949, 78.3995],
        "Rachakonda Commissionerate": [17.3000, 78.6000],
        "Secunderabad RP": [17.4399, 78.4983],
    }
    
    # Extract data from PDF
    print("📊 Extracting crime data from PDF...")
    district_data = []
    
    # For testing without PDF, generate sample data
    if pdf_path is None or not os.path.exists(pdf_path):
        print("⚠️ PDF not found, using sample data")
        sample_districts = [
            ["", "Adilabad", "", "", "", "", "", "", "", "4261"],
            ["", "Bhadradri Kothagudem", "", "", "", "", "", "", "", "6198"],
            ["", "Hyderabad", "", "", "", "", "", "", "", "46258"],
            ["", "Jagtial", "", "", "", "", "", "", "", "3820"],
            ["", "Jangaon", "", "", "", "", "", "", "", "2689"],
            ["", "Jayashankar Bhupalpally", "", "", "", "", "", "", "", "2355"],
            ["", "Jogulamba Gadwal", "", "", "", "", "", "", "", "1948"],
            ["", "Kamareddy", "", "", "", "", "", "", "", "2902"],
            ["", "Karimnagar", "", "", "", "", "", "", "", "5978"],
            ["", "Khammam", "", "", "", "", "", "", "", "7317"],
            ["", "Komaram Bheem Asifabad", "", "", "", "", "", "", "", "3589"],
            ["", "Mahabubabad", "", "", "", "", "", "", "", "3025"],
            ["", "Mahabubnagar", "", "", "", "", "", "", "", "5120"],
            ["", "Mancherial", "", "", "", "", "", "", "", "4415"],
            ["", "Medak", "", "", "", "", "", "", "", "4365"],
            ["", "Medchal-Malkajgiri", "", "", "", "", "", "", "", "12437"],
            ["", "Mulugu", "", "", "", "", "", "", "", "2198"],
            ["", "Nagarkurnool", "", "", "", "", "", "", "", "4319"],
            ["", "Nalgonda", "", "", "", "", "", "", "", "6875"],
            ["", "Narayanpet", "", "", "", "", "", "", "", "2131"],
            ["", "Nirmal", "", "", "", "", "", "", "", "3252"],
            ["", "Nizamabad", "", "", "", "", "", "", "", "5941"],
            ["", "Peddapalli", "", "", "", "", "", "", "", "3778"],
            ["", "Rajanna Sircilla", "", "", "", "", "", "", "", "3124"],
            ["", "Rangareddy", "", "", "", "", "", "", "", "15978"],
            ["", "Sangareddy", "", "", "", "", "", "", "", "7951"],
            ["", "Siddipet", "", "", "", "", "", "", "", "5125"],
            ["", "Suryapet", "", "", "", "", "", "", "", "5921"],
            ["", "Vikarabad", "", "", "", "", "", "", "", "4065"],
            ["", "Wanaparthy", "", "", "", "", "", "", "", "3458"],
            ["", "Warangal", "", "", "", "", "", "", "", "8751"],
            ["", "Yadadri Bhuvanagiri", "", "", "", "", "", "", "", "4589"],
            ["", "Cyberabad Commissionerate", "", "", "", "", "", "", "", "59911"],
            ["", "Rachakonda Commissionerate", "", "", "", "", "", "", "", "50348"],
            ["", "Secunderabad RP", "", "", "", "", "", "", "", "1470"],
        ]
        district_data = sample_districts
    else:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in range(29, 36):  # Extracts pages 29 to 35
                page = pdf.pages[page_num]
                tables = page.extract_table()
                if tables:
                    print(f"✅ Extracting Table from Page {page_num+1}")
                    for row in tables:
                        district_data.append(row)
    
    # Convert extracted data into DataFrame
    df = pd.DataFrame(district_data)
    
    # Select only relevant columns: District Name (Col 1) & Total Crimes (Col 9)
    df = df.iloc[:, [1, 9]]  # Keep only the relevant columns
    df.columns = ["District", "Total Crimes"]  # Rename columns
    
    # Remove header rows and empty values
    df = df.iloc[2:]  # Remove first 2 rows (headers)
    df = df.dropna()  # Drop empty rows
    
    # Convert crime numbers to integers
    df["Total Crimes"] = pd.to_numeric(df["Total Crimes"], errors="coerce")
    df = df.dropna()  # Drop rows where conversion failed
    
    # Clean district names (strip whitespace)
    df["District"] = df["District"].str.strip()
    
    # Remove the "TOTAL" row
    df = df[~df["District"].str.upper().isin(["TOTAL"])]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["District"])
    
    # List to store district crime data
    districts_with_coords = []
    
    # Process districts
    for index, row in df.iterrows():
        district = row["District"]
        crime_count = int(row["Total Crimes"])
        
        # First check manual coordinates
        if district in manual_coords:
            coords = manual_coords[district]
            print(f"📍 Using manual coordinates for {district}: {coords}")
        else:
            # Try geocoding
            coords = get_coordinates(district)
            time.sleep(0.5)  # Respect rate limits
        
        if coords:
            lat, lon = coords
            districts_with_coords.append({
                "district": district,
                "crimeCount": crime_count,
                "latitude": lat,
                "longitude": lon
            })
        else:
            print(f"⚠️ Warning: Could not geocode {district}")
    
    return districts_with_coords

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/crime-data')
def crime_data():
    # Path to your PDF file - change this to the actual path or set to None to use sample data
    pdf_path = None #r"C:\Users\kp\Downloads\Telangana_CrimeRates.pdf"
    
    # Process crime data
    districts = process_crime_data(pdf_path)
    
    # Return JSON response
    return jsonify(districts)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create HTML template
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Safe City - Telangana</title>
    
    <!-- Leaflet CSS and JS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css">
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    
    <!-- Font Awesome for icons -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/js/all.min.js"></script>
<body>
<!-- Navigation Bar -->
    <header>
    <style>
    /* Navigation Bar */
    header {
        width: 100%;
        padding: 15px 5%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #ffffff;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1000;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }

    nav {
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .logo img {
        position: absolute;  /* Keeps the logo at the top-left */
        top: -5px;  /* Adjusts distance from the top */
        left: 10px;  /* Adjusts distance from the left */
        width: 120px; /* Adjust the size as needed */
        height: auto; /* Maintains aspect ratio */
        object-fit: contain; /* Ensures the image fits well */
    }

    nav {
        position: relative; /* Ensures the logo stays inside the nav bar */
        height: 70px; /* Adjust nav height as needed */
        display: flex;
        align-items: center;
        padding-left: 150px; /* Space so nav links don't overlap the logo */
    }


    .nav-links {
        display:flex;
        list-style: none;
        display: flex;
        gap: 20px;
    }
    li {
        margin: 0 30px;  /* Adds 20px spacing on left & right */
        display: inline-block;
    }

    .nav-links li a {
        text-decoration: none;
        font-size: 18px;
        color: black;
        font-weight: 500;
        transition: 0.3s;
        color: #466f9d;
        font-family: 'Inter', sans-serif;
    }

    .nav-links li a:hover {
        color: #007bff;
        font-weight: bold;
    }

    .search-box {
        display: flex;
        align-items: center;
        border: 1px solid #ddd;
        border-radius: 20px;
        padding: 5px 10px;
        background: #f8f8f8;
    }

    .search-box input {
        border: none;
        background: transparent;
        outline: none;
        padding: 5px;
        font-size: 14px;
    }

    .search-box i {
        color: gray;
    }
    </style>
        <nav>
            <div class="logo"> 
              <img src="https://raw.githubusercontent.com/kushagrjoshi777/website-images/refs/heads/main/logo.jpg">
                
                </div>
                 
            <ul class="nav-links">
                <li><a href="#">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#map">Map</a></li>
                <li><a href="#review">Review</a></li>
            </ul>
            <div class="search-box">
                <input type="text" placeholder="Search">
                <i class="fas fa-search"></i>
            </div>
        </nav>
    </header>
<!-- Home Section -->
   
    <section class="hero">
        <style>
            section {
            padding: 100px 10%;
            text-align: center;
            }
            /* Reset and base styles */
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Arial', sans-serif;

            }
            
    
            body {
                    
                    height: auto;
                    min-height: 100vh;
                    margin: 0;
                    padding: 0;
                    
                }
                
            
    
            /* Color variables */
            :root {
                --primary-blue: #0057b3;
                --dark-blue: #021d42;
                --light-blue: #7ac0f5;
                --accent-red: #e63946;
                --white: #ffffff;
                --light-gray: #f8f9fa;
            }
    
            /* Hero section styles */
            .hero {
                min-height: 100vh;
                background: url('https://raw.githubusercontent.com/kushagrjoshi777/website-images/refs/heads/main/laptop.jpg') no-repeat center center/cover;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
    
            .hero-content {
                flex: 1;
                padding-right: 2rem;
            }
    
            .map-container {
                width: 300px;
                height: 300px;
                background: url('https://raw.githubusercontent.com/kushagrjoshi777/website-images/refs/heads/main/map_no_bg.png') no-repeat center center/cover;
                border-radius: 10px;
                position: relative;
                overflow: hidden;
            }
    
            .map-grid {
                width: 100%;
                height: 100%;
                background-image: 
                    linear-gradient(to right, rgba(255,206,0,0.1) 1px, transparent 1px),
                    linear-gradient(to bottom, rgba(255,206,0,0.1) 1px, transparent 1px);
                background-size: 50px 50px;
            }
    
            .map-pin {
                position: absolute;
                top: 30%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 50px;
                height: 50px;
                color: var(--accent-red);
                font-size: 50px;
            }
            .hero::before {
                content: "";
                position: absolute;
                inset: 0;
                background: rgba(0, 0, 0, 0.5); /* dark overlay */
                z-index: 0;
            }
            
            .hero-content {
                position: relative;
                z-index: 1;
            }
            
    
            .hero-subtitle {
                text-transform: uppercase;
                color: var(--white);
                font-weight: bold;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }
    
            .hero-title {
                font-size: 2.5rem;
                color: var(--white);
                margin-bottom: 1.5rem;
                line-height: 1.2;
            }
    
            .hero-description {
                color: var(--light-gray);
                margin-bottom: 2rem;
                line-height: 1.6;
            }
    
            .cta-button {
                display: inline-block;
                background-color: var(--primary-blue);
                color: var(--white);
                padding: 0.75rem 1.5rem;
                border-radius: 4px;
                text-decoration: none;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }
    
            .cta-button:hover {
                background-color: var(--dark-blue);
            }
    
            .social-links {
                display: flex;
                margin-top: 2rem;
            }
    
            .social-link {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background-color: var(--white);
                color: var(--primary-blue);
                margin-right: 0.75rem;
                text-decoration: none;
                transition: all 0.3s ease;
            }
    
            .social-link:hover {
                background-color: var(--primary-blue);
                color: var(--white);
            }
    
            /* Responsive styles */
            @media (max-width: 968px) {
                .hero {
                    flex-direction: column;
                }
    
                .hero-content {
                    margin-bottom: 3rem;
                    padding-right: 0;
                }
    
                .hero-image {
                    justify-content: flex-start;
                }
            }
    
            @media (max-width: 768px) {
                header {
                    flex-direction: column;
                    align-items: flex-start;
                }
    
                }
    
        </style>
        <section class="hero">
            <div class="hero-content">
                <p class="hero-subtitle">THE PERFECT RESOURCE TO A SAFE CITY</p>
                <h1 class="hero-title">CITY SAFE</h1>
                <p class="hero-description">
                    Stay Safe, Stay Informed.<br>
                    Our app provides real-time safety insights with location-specific reports. AI-driven analytics to help you avoid danger zones. Navigate your city confidently with real-time updates and emergency assistance at your fingertips.
                </p>
                <a href="#" class="cta-button">Download Now</a>
                <div class="social-links">
                    <a href="#" class="social-link"><i class="fab fa-facebook-f"></i></a>
                    <a href="#" class="social-link"><i class="fab fa-twitter"></i></a>
                    <a href="#" class="social-link"><i class="fab fa-instagram"></i></a>
                </div>
            </div>
            <div class="hero-image">
                <div class="map-container">
                    <div class="map-grid"></div>
                    <i class="fas fa-map-marker-alt map-pin"></i>
                </div>
            </div>
        </section>
    
        <script>
            // Add active class to current navigation item
            const currentLocation = location.href;
            const navItems = document.querySelectorAll('nav ul li a');
            
            navItems.forEach(item => {
                if(item.href === currentLocation) {
                    item.classList.add('active');
                }
            });
    
            // Simple map pin animation
            const mapPin = document.querySelector('.map-pin');
            let pinOffset = 0;
            
            setInterval(() => {
                pinOffset = pinOffset === 0 ? -5 : 0;
                mapPin.style.transform = `translate(-50%, ${pinOffset}px)`;
            }, 1000);
        </script>
    </section>
    </body>
    </html>
<!-- About Section -->
    <section id="about" class="about-section">
    <style>
    .about-section {
    background: linear-gradient(to bottom, #676666, #ffffff);
    background-color: white;
    padding-top: 100px;
    padding-bottom: 100px;
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    position: relative;
    width: 100%;
    height: 100vh;}
    
    .wave-bg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 50vh;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320"><path fill="%23add8e6" fill-opacity="1" d="M0,192L80,186.7C160,181,320,171,480,186.7C640,203,800,245,960,229.3C1120,213,1280,139,1360,101.3L1440,64V320H0Z"></path></svg>') no-repeat;
    background-size: cover;
    z-index: -1;
}

    .about-content h1 {
            font-family: 'Volkhov', serif;
            font-size: 45px;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 20px;
            color: black;
        }
    .about-content p {
            font-size: 18px;
            font-weight: 400;
            color: #333;
            line-height: 1.6;
        }
    .about-content p strong {
    color: #3d638d; /* Same color as navigation */
    font-weight: 600;}
    </style>
        <div class="wave-bg"></div>
        <div class="about-content">
            <h1>ABOUT CITY SAFE</h1>
            <p>
                An app designed to help users identify safe and unsafe areas within a city in real-time. 
                Using a combination of crime data, user reports, and AI analysis, the app provides an 
                interactive map highlighting high-risk zones and safe routes.
            </p>
            <p>
                It features live alerts, safety ratings, and emergency assistance options, making it ideal for 
                travelers, commuters, and residents who want to navigate urban areas securely. With its 
                user-friendly interface and community-driven updates, City Safe empowers individuals to make 
                informed decisions about their surroundings, enhancing personal safety and awareness.
            </p>
        </div>
    </section>

<!-- Map Section -->
 <style>
        :root {
            --primary-color: #3498db;
            --secondary-color: #2c3e50;
            --success-color: #2ecc71;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
            --light-color: #ecf0f1;
            --dark-color: #34495e;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f7fa;
            color: var(--dark-color);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1.5rem;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .header h1 {
            margin-bottom: 0.5rem;
            color: var(--secondary-color);
        }
        
        .header p {
            color: #7f8c8d;
            max-width: 700px;
            margin: 0 auto;
        }
        
        .card {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            overflow: hidden;
            margin-bottom: 2rem;
        }
        
        .card-header {
            background-color: var(--light-color);
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .card-body {
            padding: 1.5rem;
        }
        
        #map {
            height: 500px;
            width: 100%;
            border-radius: 10px;
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            font-size: 1rem;
        }
        
        .btn-primary {
            background-color: var(--primary-color);
            color: white;
        }
        
        .btn-primary:hover {
            background-color: #2980b9;
        }
        
        .btn-secondary {
            background-color: var(--secondary-color);
            color: white;
        }
        
        .btn-secondary:hover {
            background-color: #1a2530;
        }
        
        .controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        
        #status {
            padding: 0.75rem;
            border-radius: 5px;
            margin-bottom: 1rem;
            background-color: #f8f9fa;
            display: none;
        }
        
        #status.visible {
            display: block;
        }
        
        .status-info {
            background-color: var(--primary-color);
            color: white;
        }
        
        .status-success {
            background-color: var(--success-color);
            color: white;
        }
        
        .status-warning {
            background-color: var(--warning-color);
            color: white;
        }
        
        .status-error {
            background-color: var(--danger-color);
            color: white;
        }
        
        .legend {
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            margin-top: 1rem;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
        }
        
        .color-high {
            background-color: var(--danger-color);
        }
        
        .color-moderate {
            background-color: var(--warning-color);
        }
        
        .color-low {
            background-color: var(--success-color);
        }
        
        .info-cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }
        
        .info-card {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .info-card-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .info-card-header i {
            font-size: 1.5rem;
            color: var(--primary-color);
        }
        
        .info-card h3 {
            margin: 0;
            color: var(--dark-color);
        }
        
        .crime-stats {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .stat-card {
            flex: 1;
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            text-align: center;
        }
        
        .stat-card h3 {
            color: var(--dark-color);
            margin-bottom: 0.5rem;
        }
        
        .stat-card .number {
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .stat-card.danger .number {
            color: var(--danger-color);
        }
        
        .stat-card.warning .number {
            color: var(--warning-color);
        }
        
        .stat-card.success .number {
            color: var(--success-color);
        }
        
        .marker-pin {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background-color: red;
            opacity: 0.7;
            border: 2px solid darkred;
        }
        
        .marker-label {
            font-size: 12px;
            font-weight: bold;
            color: #333;
            text-align: center;
            margin-top: 5px;
        }
        
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid rgba(0, 0, 0, 0.1);
            border-top-color: var(--primary-color);
            border-radius: 50%;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        footer {
            background-color: var(--secondary-color);
            color: white;
            text-align: center;
            padding: 2rem 0;
            margin-top: 3rem;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            #map {
                height: 400px;
            }
            
            .crime-stats {
                flex-direction: column;
            }
            
           
            }
        }
    </style>
</head>
<body>
<!-- Loading overlay -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
    </div>
    <div class="container">
        <div class="header">
            <h1>Crime Map</h1>
            <p>Explore district-wise crime data in  to stay informed and make safer decisions.</p>
        </div>
        
        <div id="status" class="status-info"></div>
        
        <div class="card">
            <div class="card-header">
                <span>Crime Map by District</span>
                <div>
                    <select id="dataView">
                        <option value="districts">District View</option>
                        <option value="heatmap">Heatmap View</option>
                    </select>
                </div>
            </div>
            <div class="card-body">
                <div class="controls">
                    <button id="resetBtn" class="btn btn-secondary">
                        <i class="fas fa-undo"></i> Reset Map
                    </button>
                    <button id="locateBtn" class="btn btn-primary">
                        <i class="fas fa-map-marker-alt"></i> Show My Location
                    </button>
                </div>
                
                <div id="map"></div>
                
                <div class="legend">
                    <h3>Crime Level Indicators</h3>
                    <div class="legend-item">
                        <div class="legend-color color-high"></div>
                        <span>High Crime Rate (>10000 cases)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color color-moderate"></div>
                        <span>Moderate Crime Rate (5000-10000 cases)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color color-low"></div>
                        <span>Low Crime Rate (<5000 cases)</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="crime-stats">
            <div class="stat-card danger">
                <h3>High Risk Districts</h3>
                <div class="number" id="highRiskCount">0</div>
                <p>Districts with >10,000 cases</p>
            </div>
            <div class="stat-card warning">
                <h3>Moderate Risk Districts</h3>
                <div class="number" id="moderateRiskCount">0</div>
                <p>Districts with 5,000-10,000 cases</p>
            </div>
            <div class="stat-card success">
                <h3>Low Risk Districts</h3>
                <div class="number" id="lowRiskCount">0</div>
                <p>Districts with <5,000 cases</p>
            </div>
        </div>
        
        <div class="info-cards">
            <div class="info-card">
                <div class="info-card-header">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Data Sources</h3>
                </div>
                <p>This map visualizes crime data extracted from the Telangana State Crime Report. The data shows total crime cases reported across different districts.</p>
                <p>The red markers represent district centers, with labels showing district name and total number of cases.</p>
            </div>
            
            <div class="info-card">
                <div class="info-card-header">
                    <i class="fas fa-lightbulb"></i>
                    <h3>Safety Tips</h3>
                </div>
                <ul>
                    <li>Be aware of your surroundings, especially in high-risk areas</li>
                    <li>Keep valuables secure and out of sight</li>
                    <li>Travel in groups when possible in less familiar areas</li>
                    <li>Share your location with trusted contacts when traveling</li>
                </ul>
            </div>
            
            <div class="info-card">
                <div class="info-card-header">
                    <i class="fas fa-info-circle"></i>
                    <h3>About This Tool</h3>
                </div>
                <p>This tool combines data extraction from PDF reports with interactive mapping to help citizens make informed decisions about safety.</p>
                <p>The map highlights crime hotspots across Telangana districts based on official crime statistics.</p>
            </div>
        </div>
    </div>
    
    <footer>
        <p>&copy; 2025 Safe City | Privacy Policy | Terms of Service</p>
    </footer>
    
    <script>
        // Initialize map centered on Telangana
        let map = L.map('map').setView([17.5, 78.5], 7);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.carto.com/">CartoDB</a> contributors',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(map);
        
        // Variables to track markers and data
        let districtMarkers = L.layerGroup().addTo(map);
        let statusElement = document.getElementById('status');
        let loadingOverlay = document.getElementById('loadingOverlay');
        let districtData = [];
        // Show loading overlay
        function showLoading() {
            loadingOverlay.style.display = 'flex';
        }
        
        // Hide loading overlay
        function hideLoading() {
            loadingOverlay.style.display = 'none';
        }
        
        // Initialize event listeners
        document.getElementById('resetBtn').addEventListener('click', resetMap);
        document.getElementById('dataView').addEventListener('change', function() {
            renderMap(districtData);
        });
        document.getElementById('locateBtn').addEventListener('click', getUserLocation);
        
        // Function to get and display user location
        function getUserLocation() {
            if (navigator.geolocation) {
                updateStatus('Fetching your location...', 'status-info');
                
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        // Success callback
                        const userLat = position.coords.latitude;
                        const userLng = position.coords.longitude;
                        
                        // Add a special marker for user location
                        const userIcon = L.divIcon({
                            className: 'user-location-marker',
                            html: `
                                <div style="background-color: #3498db; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>
                                <div style="font-weight: bold; text-align: center; margin-top: 5px;">Your Location'</div>
                            `,
                            iconSize: [40, 40],
                            iconAnchor: [20, 20]
                        });
                        
                        const userMarker = L.marker([userLat, userLng], {
                            icon: userIcon
                        }).addTo(map);
                        
                        userMarker.bindPopup('<strong>Your Location</strong>').openPopup();
                        
                        // Center the map on user's location with a closer zoom
                        map.setView([userLat, userLng], 10);
                        
                        updateStatus('Your location detected!', 'status-success');
                        setTimeout(() => {
                            statusElement.classList.remove('visible');
                        }, 3000);
                    },
                    function(error) {
                        // Error callback
                        let errorMessage;
                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                errorMessage = "Location access denied. Please enable location services.";
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMessage = "Location information unavailable.";
                                break;
                            case error.TIMEOUT:
                                errorMessage = "Location request timed out.";
                                break;
                            default:
                                errorMessage = "An unknown error occurred while getting location.";
                        }
                        updateStatus(errorMessage, 'status-warning');
                    }
                );
            } else {
                updateStatus('Geolocation is not supported by your browser.', 'status-error');
            }
        }
        
        // Fetch crime data from API
        async function fetchCrimeData() {
            showLoading();
            updateStatus('Fetching crime data...', 'status-info');
            
            try {
                const response = await fetch('/api/crime-data');
                const data = await response.json();
                hideLoading();
                updateStatus('Crime data loaded successfully!', 'status-success');
                
                // Save data and render map
                districtData = data;
                renderMap(data);
                
                // Hide status after delay
                setTimeout(() => {
                    statusElement.classList.remove('visible');
                }, 3000);
                
            } catch (error) {
                hideLoading();
                updateStatus('Error loading crime data. Please try again later.', 'status-error');
                console.error('Error fetching crime data:', error);
            }
        }
        
        // Render crime data on map
        function renderMap(data) {
            // Clear previous markers
            districtMarkers.clearLayers();
            
            // Get view preference
            const viewMode = document.getElementById('dataView').value;
            
            // Variables to count risk levels
            let highRisk = 0, moderateRisk = 0, lowRisk = 0;
            
            // Process each district
            data.forEach(district => {
                // Determine risk level based on crime count
                // Determine risk level based on crime count
            let riskLevel, color, radius;
            if (district.crimeCount > 10000) {
                riskLevel = 'high';
                color = '#e74c3c'; // danger color
                radius = 6000;
                highRisk++;
            } else if (district.crimeCount >= 5000) {
                riskLevel = 'moderate';
                color = '#f39c12'; // warning color
                radius = 5000;
                moderateRisk++;
            } else {
                riskLevel = 'low';
                color = '#2ecc71'; // success color
                radius = 4000;
                lowRisk++;
            }
                
                if (viewMode === 'heatmap') {
                    // Create circle for heatmap view
                    let circle = L.circle([district.latitude, district.longitude], {
                        color: color,
                        fillColor: color,
                        fillOpacity: 0.5,
                        radius: radius
                    }).bindPopup(`
                        <strong>${district.district}</strong><br>
                        Total Crime Cases: ${district.crimeCount}<br>
                        Risk Level: ${riskLevel.toUpperCase()}
                    `);
                    
                    districtMarkers.addLayer(circle);
                } else {
                    // Create custom HTML icon for district view
                    let icon = L.divIcon({
                        className: 'custom-marker',
                        html: `
                            <div class="marker-pin" style="background-color: ${color}"></div>
                            <div class="marker-label">${district.district}<br>${district.crimeCount}</div>
                        `,
                        iconSize: [40, 40],
                        iconAnchor: [20, 20]
                    });
                    
                    let marker = L.marker([district.latitude, district.longitude], {
                        icon: icon
                    }).bindPopup(`
                        <strong>${district.district}</strong><br>
                        Total Crime Cases: ${district.crimeCount}<br>
                        Risk Level: ${riskLevel.toUpperCase()}
                    `);
                    
                    districtMarkers.addLayer(marker);
                }
            });
            
            // Update statistics
            document.getElementById('highRiskCount').textContent = highRisk;
            document.getElementById('moderateRiskCount').textContent = moderateRisk;
            document.getElementById('lowRiskCount').textContent = lowRisk;
        }
        
        // Reset map
        function resetMap() {
            map.setView([17.5, 78.5], 7);
            updateStatus('Map has been reset.', 'status-success');
            setTimeout(() => {
                statusElement.classList.remove('visible');
            }, 3000);
        }
        
        // Update status message
        function updateStatus(message, className) {
            statusElement.textContent = message;
            statusElement.className = className;
            statusElement.classList.add('visible');
        }
        
        // Show about message
        function showAbout() {
            alert('Safe City - Telangana is a crime mapping application that visualizes district-level crime data extracted from the Telangana State Crime Report. This tool helps citizens stay informed about crime patterns across different districts.');
        }
        
        // Load data on page load
        window.onload = function() {
            setTimeout(() => {
                map.invalidateSize();
                fetchCrimeData();
            }, 100);
        }
    </script>
</body>
<!-- Review Section -->
    <section id="review" class="review-section">
            <h1>User Reviews</h1>
            <p>Read what users are saying about City Safe.</p>
        <style>
        /* Add this to the review-section style */
        .review-section {
        background-color: #f1f1f1;
        padding: 50px 0;
        text-align: center;
        z-index: 1; /* Ensure it stays below the map section */
        position: relative;
        }
        
        }
        .review-section h1 {
        font-family: 'Volkhov', serif;
        font-size: 45px;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 20px;
        color: black;
        }
        .container {
        max-width: 1200px;
        margin: 0 auto;
        }
        header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        background: linear-gradient(to right, #fff 50%, #ffdcb3 50%);
        }

        .logo {
        display: flex;
        align-items: center;
        gap: 10px;
        }

        .logo img {
        height: auto;
        }

        .logo-text {
        font-size: 24px;
        font-weight: bold;
        color: #333;
        }

        nav {
        display: flex;
        justify-content: space-between; /* Ensures even spacing */
        align-items: center; /* Aligns items vertically */
        background-color: #ffffff; /* Ensures a white background */
        padding: 15px 30px; /* Adds padding for spacing */
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); /* Optional: Subtle shadow */
        position: fixed; /* Keeps navbar fixed at top */
        width: 100%; /* Full width */
        top: 0;
        left: 0;
        z-index: 1000;
        }


        nav a {
        text-decoration: none;
        color: black;
        padding: 10px 15px;
        font-size: 16px;
        transition: 0.3s;
        }

        nav a.active {
        color: #3d638d; /* Same color as navigation */
        }

        .search-box {
        display: flex;
        align-items: center;
        background-color: #fff;
        border-radius: 20px;
        padding: 5px 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .search-box input {
        border: none;
        outline: none;
        padding: 5px;
        width: 150px;
        }

    /* Main content */
        .main-content {
        display: flex;
        margin-top: 20px;
        min-height: 500px;
        }

    /* Contact info section */
        .contact-info {
        background-color: #515151;
        color: #fff;
        padding: 30px;
        border-radius: 8px;
        width: 35%;
        position: relative;
        overflow: hidden;
        }

        .contact-info h2 {
        margin-bottom: 10px;
        font-size: 24px;
        }

        .contact-info p {
        margin-bottom: 30px;
        font-size: 16px;
        }

        .contact-details {
        margin-top: 50px;
        }

        .contact-item {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        font-size: 16px;
        }

        .contact-item i {
        margin-right: 15px;
        width: 20px;
        text-align: center;
        }


        .social-link {
        width: 30px;
        height: 30px;
        background-color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: black;
        cursor: pointer;
        }

        .social-link.active {
        background-color: #fff;
        }

    /* Decorative circles */
        .circle {
        position: absolute;
        bottom: -100px;
        right: -50px;
        width: 200px;
        height: 200px;
        background-color: rgba(48, 50, 52, 0.5);
        border-radius: 50%;
        z-index: 0;
        }

        .circle-inner {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100px;
        height: 100px;
        background-color: rgba(36, 39, 44, 0.8);
        border-radius: 50%;
        }

    /* Contact form */
        .contact-form {
        background-color: #fff;
        padding: 142px;
        border-radius: 8px;
        width: 65%;
        }

        .form-row {
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
        }

        .form-group {
        flex: 1;
        }

        .form-group label {
        display: block;
        margin-bottom: 23px;
        color: #555;
        }

        .form-group input, 
        .form-group textarea {
        width: 100%;
        padding: 14px;
        border: none;
        border-bottom: 1px solid #ddd;
        outline: none;
        }

        .radio-group {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin-top: 10px;
        }   

        .radio-option {
        display: flex;
        align-items: center;
        gap: 5px;
        }

        .radio-custom {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border: 2px solid #ddd;
        display: inline-block;
        position: relative;
        }

        .radio-custom.active::after {
        content: "";
        position: absolute;
        top: 3px;
        left: 3px;
        width: 10px;
        height: 10px;
        background-color: #000;
        border-radius: 50%;
        }

        .radio-option.inactive .radio-custom::after {
        background-color: #ddd;
        }

        .btn-submit {
        background-color: #3f3f43;
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 30px;
        cursor: pointer;
        float: right;
        margin-top: 20px;
        font-size: 16px;
        }

        </style>

        <div class="main-content">
            <div class="contact-info">
                <h2>Contact Information</h2>
                <p>Say something to start a live chat</p>

                <div class="contact-details">
                    <div class="contact-item">
                        <i>📞</i>
                        <span>+91 7302480404</span>
                    </div>
                    <div class="contact-item">
                        <i>📧</i>
                        <span>citysafe2025@gmail.com</span>
                    </div>
                    <div class="contact-item">
                        <i>📍</i>
                        <span>SRM COLLEGE OF ENGINEERING KATTANKULATHUR</span>
                    </div>
                </div>


                <div class="circle">
                    <div class="circle-inner"></div>
                </div>
                <div class="Big_circle">
                    <div class=""Big_circle-inner></div>
                </div>
            </div>

            <div class="contact-form">
                <div class="form-row">
                    <div class="form-group">
                        <label>First Name</label>
                        <input type="text">
                    </div>
                    <div class="form-group">
                        <label>Last Name</label>
                        <input type="text">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email">
                    </div>
                    <div class="form-group">
                        <label>Phone Number</label>
                        <input type="tel">
                    </div>
                </div>

                <div class="form-group">
                    <label>Select Subject?</label>
                    <div class="radio-group">
                        <div class="radio-option">
                            <div class="radio-custom active"></div>
                            <span>General Inquiry</span>
                        </div>
                        <div class="radio-option inactive">
                            <div class="radio-custom"></div>
                            <span>Technical Support</span>
                        </div>
                        <div class="radio-option inactive">
                            <div class="radio-custom"></div>
                            <span>Feedback & Suggestions</span>
                        </div>
                        <div class="radio-option inactive">
                            <div class="radio-custom"></div>
                            <span>Other</span>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <textarea rows="4" placeholder="Write your message..."></textarea>
                </div>

                <button class="btn-submit">Send Message</button>
            </div>
        </div>
    </div>

    <script>
        // Add basic interactivity
        document.addEventListener('DOMContentLoaded', function() {
            // Radio button functionality
            const radioOptions = document.querySelectorAll('.radio-option');
            
            radioOptions.forEach(option => {
                option.addEventListener('click', function() {
                    // Remove active class from all options
                    radioOptions.forEach(opt => {
                        opt.classList.add('inactive');
                        opt.classList.remove('active');
                        opt.querySelector('.radio-custom').classList.remove('active');
                    });
                    
                    // Add active class to clicked option
                    this.classList.remove('inactive');
                    this.classList.add('active');
                    this.querySelector('.radio-custom').classList.add('active');
                });
            });

            // Form submission (prevent default behavior)
            const form = document.querySelector('.contact-form');
            const submitBtn = document.querySelector('.btn-submit');
            
            submitBtn.addEventListener('click', function(e) {
                e.preventDefault();
                alert('Form submitted! (This is just a demo)');
            });
        });
    </script> 

    </body>
</html>''')
        # Enhanced version of the get_coordinates function to be more robust
def get_coordinates_by_address(address, state="Telangana", country="India"):
    """Get coordinates for an address string using Nominatim OpenStreetMap API"""
    print(f"🔍 Geocoding address: {address}...", end="", flush=True)
    
    base_url = "https://nominatim.openstreetmap.org/search"
    
    # Append state and country for better results
    query = f"{address}, {state}, {country}"
    
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
    }
    
    # Add a user-agent to comply with Nominatim usage policy
    headers = {
        "User-Agent": "TelanganaDistrict_CrimeMap/1.0"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        # If we got results, return the first one's coordinates
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f" ✅ Found: [{lat}, {lon}]")
            return [lat, lon]
        else:
            print(f" ❌ Not found")
            return None
    except Exception as e:
        print(f" ❌ Error: {str(e)[:50]}...")
        return None

# Add a route to get nearest districts based on user location
@app.route('/api/nearby-districts')
def nearby_districts():
    try:
        # Get user coordinates from request parameters
        user_lat = float(request.args.get('lat'))
        user_lng = float(request.args.get('lng'))
        
        # Process crime data to get all district data
        pdf_path = r"C:\Users\kp\Downloads\TELANGANA STATE CRIME STATEMENT.pdf"
        all_districts = process_crime_data(pdf_path)
        
        # Calculate distance to each district
        for district in all_districts:
            district_lat = district['latitude']
            district_lng = district['longitude']
            
            # Simple distance calculation (Euclidean, not perfect but sufficient for basic proximity)
            # For more accuracy, Haversine formula would be better
            distance = ((user_lat - district_lat) ** 2 + (user_lng - district_lng) ** 2) ** 0.5
            district['distance'] = distance
        
        # Sort by distance
        nearby = sorted(all_districts, key=lambda x: x['distance'])
        
        # Return the 5 closest districts
        return jsonify(nearby[:5])
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Add a route to geocode an address
@app.route('/api/geocode')
def geocode_address():
    try:
        address = request.args.get('address')
        if not address:
            return jsonify({"error": "Address parameter is required"}), 400
            
        coordinates = get_coordinates_by_address(address)
        if coordinates:
            return jsonify({
                "success": True,
                "latitude": coordinates[0],
                "longitude": coordinates[1]
            })
        else:
            return jsonify({"success": False, "error": "Could not geocode the address"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Add a route to provide safety recommendations based on location
@app.route('/api/safety-tips')
def safety_recommendations():
    try:
        # Get user coordinates and nearby district
        user_lat = float(request.args.get('lat'))
        user_lng = float(request.args.get('lng'))
        district_name = request.args.get('district')
        
        # Process crime data to get risk level
        pdf_path = None  # r"C:\Users\kp\Downloads\TELANGANA STATE CRIME STATEMENT.pdf"
        all_districts = process_crime_data(pdf_path)
        
        # Find the district by name
        district_data = next((d for d in all_districts if d['district'].lower() == district_name.lower()), None)
        
        if district_data:
            crime_count = district_data['crimeCount']
            
            # Determine risk level
            if crime_count > 1000:
                risk_level = "high"
                tips = [
                    "Avoid traveling alone, especially at night",
                    "Keep valuables secure and out of sight",
                    "Stay in well-lit and populated areas",
                    "Share your live location with family members",
                    "Keep emergency contacts easily accessible"
                ]
            elif crime_count >= 5000:
                risk_level = "moderate"
                tips = [
                    "Be aware of your surroundings",
                    "Avoid displaying expensive items in public",
                    "Travel in groups when possible",
                    "Keep your phone charged for emergencies",
                    "Know the nearest police stations"
                ]
            else:
                risk_level = "low"
                tips = [
                    "Basic precautions are still recommended",
                    "Keep emergency contact numbers handy",
                    "Be cautious in unfamiliar areas",
                    "Lock vehicles and homes securely",
                    "Report any suspicious activities"
                ]
            
            return jsonify({
                "district": district_name,
                "riskLevel": risk_level,
                "crimeCount": crime_count,
                "safetyTips": tips
            })
        else:
            return jsonify({"error": "District not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# When running the app, make it more production-ready
if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create HTML template (your existing code for this)
    
    # Add better error logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='app.log'
    )
    
    print("🚀 Starting Safe City - Telangana application...")
    print("📊 Crime data will be loaded on first request")
    print("📱 Access the application at http://127.0.0.1:5000")
    app.run(debug=True)
