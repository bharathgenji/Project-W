"""
Seed the Firestore emulator with rich, realistic demo data for BuildScope.
50+ leads across all trades, cities, values — designed to impress on a demo.
"""
from __future__ import annotations
import os, sys
from datetime import datetime, timezone, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8681")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "projectw-e3d92")

from shared.clients.firestore_client import FirestoreClient
from shared.utils import generate_id, extract_keywords

db = FirestoreClient.get_instance("projectw-e3d92")

def d(days_ago):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).replace(tzinfo=None).isoformat()

def deadline(days_from_now):
    return (datetime.now(timezone.utc) + timedelta(days=days_from_now)).replace(tzinfo=None).isoformat()

LEADS = [
  # ── FEDERAL BIDS (high value, SAM.gov) ────────────────────────────────────
  {"type":"bid","trade":"ELECTRICAL","title":"Federal: Electrical Systems Upgrade — DHS Headquarters Campus, Phase 2","value":3_800_000,
   "addr":"Nebraska Ave NW, Washington, DC 20528","owner":{"n":"Dept of Homeland Security","p":"+12024471000","e":"procurement@dhs.gov"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(1),"deadline":deadline(21),"src":"sam.gov","score":97,
   "ai":{"project_type":"renovation","owner_type":"institutional","sqft":180000,"key_materials":["conduit","switchgear","UPS systems"]}},

  {"type":"bid","trade":"HVAC","title":"Federal: HVAC Replacement + Energy Retrofit — VA Medical Center Chicago","value":6_200_000,
   "addr":"820 S Damen Ave, Chicago, IL 60612","owner":{"n":"Dept of Veterans Affairs","p":"+13125690400","e":"bids@va.gov"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(2),"deadline":deadline(35),"src":"sam.gov","score":96,
   "ai":{"project_type":"renovation","owner_type":"institutional","units":450,"key_materials":["chiller","AHU","BAS controls"]}},

  {"type":"bid","trade":"CONCRETE","title":"Federal: Parking Garage Structural Repair — GSA Federal Building Dallas","value":2_100_000,
   "addr":"1100 Commerce St, Dallas, TX 75242","owner":{"n":"General Services Administration","p":"+12146553000","e":"bids@gsa.gov"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(3),"deadline":deadline(28),"src":"sam.gov","score":91,
   "ai":{"project_type":"repair","owner_type":"institutional","sqft":95000,"key_materials":["structural concrete","epoxy injection","waterproofing"]}},

  {"type":"bid","trade":"ROOFING","title":"Federal: Full Roof Replacement — USPS Distribution Center Phoenix","value":875_000,
   "addr":"4949 E Van Buren St, Phoenix, AZ 85008","owner":{"n":"US Postal Service","p":"+16025286300","e":"facilities@usps.gov"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(4),"deadline":deadline(18),"src":"sam.gov","score":88,
   "ai":{"project_type":"renovation","owner_type":"institutional","sqft":120000,"key_materials":["TPO membrane","ISO insulation","metal edge"]}},

  {"type":"bid","trade":"PLUMBING","title":"Federal: Plumbing Infrastructure Modernization — Army Reserve Center","value":1_450_000,
   "addr":"2600 Cullen Blvd, Houston, TX 77004","owner":{"n":"US Army Corps of Engineers","p":"+17136701100","e":"procurement@usace.army.mil"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(5),"deadline":deadline(42),"src":"sam.gov","score":89,
   "ai":{"project_type":"renovation","owner_type":"institutional","key_materials":["copper pipe","backflow preventers","fire suppression"]}},

  # ── HIGH-VALUE COMMERCIAL PERMITS ─────────────────────────────────────────
  {"type":"permit","trade":"ELECTRICAL","title":"ELECTRICAL - New 35-story mixed-use tower, full electrical rough-in and service","value":8_500_000,
   "addr":"350 N Michigan Ave, Chicago, IL 60601","owner":{"n":"Lakefront Development LLC","p":"+13125550192","e":"dev@lakefrontdev.com"},
   "gc":{"n":"Turner Construction","p":"+13125558800","lic":"IL-GC-00019"},"status":"active","posted":d(2),"src":"chicago-ydr8-5enu","score":94,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","sqft":420000,"units":35,"key_materials":["switchgear","busduct","generators"]}},

  {"type":"permit","trade":"HVAC","title":"HVAC - 28-story office tower full mechanical system, new construction","value":4_200_000,
   "addr":"1000 Main St, Houston, TX 77002","owner":{"n":"Main Street Tower Partners","p":"+17135553300","e":"projects@mstower.com"},
   "gc":{"n":"Skanska USA","p":"+17135559900","lic":"TX-GC-88821"},"status":"active","posted":d(1),"src":"houston-djnh-at8a","score":93,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","sqft":310000,"key_materials":["VAV systems","cooling towers","BMS"]}},

  {"type":"permit","trade":"CONCRETE","title":"CONCRETE - 400-unit luxury apartment foundation and structural frame","value":11_200_000,
   "addr":"2800 Post Oak Blvd, Houston, TX 77056","owner":{"n":"Post Oak Residential LLC","p":"+17135554400","e":""},
   "gc":{"n":"DPR Construction","p":"+17135557700","lic":"TX-GC-44321"},"status":"active","posted":d(3),"src":"houston-djnh-at8a","score":95,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","units":400,"sqft":520000,"key_materials":["post-tension slab","rebar","formwork"]}},

  {"type":"permit","trade":"ROOFING","title":"ROOFING - Amazon fulfillment center 500,000 sqft roof replacement","value":2_800_000,
   "addr":"8000 Tradeport Dr, Orlando, FL 32827","owner":{"n":"Amazon Fulfillment Services","p":"+14075558800","e":"facilities@amazon.com"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(6),"src":"orlando","score":90,
   "ai":{"project_type":"renovation","owner_type":"large_commercial","sqft":500000,"key_materials":["thermoplastic membrane","tapered insulation"]}},

  {"type":"permit","trade":"ELECTRICAL","title":"ELECTRICAL - Solar + battery storage 2MW, commercial rooftop array","value":3_100_000,
   "addr":"4400 W Sunset Blvd, Los Angeles, CA 90029","owner":{"n":"Sunset Media Group","p":"+13235551234","e":"ops@sunsetmedia.com"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(4),"src":"losangeles-yv23-pmwf","score":88,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","key_materials":["solar panels","lithium battery storage","inverters","meters"]}},

  # ── MID-SIZE COMMERCIAL ────────────────────────────────────────────────────
  {"type":"permit","trade":"PLUMBING","title":"PLUMBING - Hotel renovation, 220 rooms full plumbing replacement","value":890_000,
   "addr":"500 N Lake Shore Dr, Chicago, IL 60611","owner":{"n":"Marriott Hotels","p":"+13125556600","e":"facilities@marriott.com"},
   "gc":{"n":"Pepper Construction","p":"+13125553300","lic":"IL-GC-55511"},"status":"active","posted":d(7),"src":"chicago-ydr8-5enu","score":82,
   "ai":{"project_type":"renovation","owner_type":"large_commercial","units":220,"key_materials":["PEX","cast iron","grease interceptor"]}},

  {"type":"permit","trade":"ELECTRICAL","title":"ELECTRICAL - Data center UPS and generator installation, 2MVA capacity","value":1_600_000,
   "addr":"2001 Westlake Ave, Seattle, WA 98109","owner":{"n":"Pacific Northwest Cloud LLC","p":"+12065559900","e":""},
   "gc":{"n":"McKinstry","p":"+12065552200","lic":"WA-EC-91234"},"status":"active","posted":d(5),"src":"seattle","score":85,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","key_materials":["generators","UPS","switchgear","PDU"]}},

  {"type":"permit","trade":"HVAC","title":"HVAC - 12-story Class A office building full system replacement","value":750_000,
   "addr":"1401 Brickell Ave, Miami, FL 33131","owner":{"n":"Brickell Capital Properties","p":"+13055558800","e":"pm@brickellcap.com"},
   "gc":{"n":"Moss Construction","p":"+13055553300","lic":"FL-CGC-055111"},"status":"active","posted":d(8),"src":"miami-dade","score":79,
   "ai":{"project_type":"renovation","owner_type":"large_commercial","sqft":145000,"key_materials":["VRF","chillers","DOAS"]}},

  {"type":"permit","trade":"ROOFING","title":"ROOFING - Retail strip center 8-building complex re-roof with solar prep","value":420_000,
   "addr":"15000 Pines Blvd, Pembroke Pines, FL 33027","owner":{"n":"Cornerstone Retail REIT","p":"+19545558800","e":""},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(9),"src":"miami-dade","score":74,
   "ai":{"project_type":"renovation","owner_type":"large_commercial","sqft":85000,"key_materials":["TPO","ISO","gutters"]}},

  {"type":"permit","trade":"CONCRETE","title":"CONCRETE - Parking garage 600-space new construction, cast-in-place","value":5_400_000,
   "addr":"3000 Peachtree Rd NE, Atlanta, GA 30305","owner":{"n":"Peachtree Development Corp","p":"+14045558800","e":"dev@peachtreedcorp.com"},
   "gc":{"n":"Brasfield & Gorrie","p":"+14045554400","lic":"GA-GC-CR001"},"status":"active","posted":d(10),"src":"atlanta","score":86,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","units":600,"key_materials":["post-tension","structural concrete","waterproofing"]}},

  # ── RESIDENTIAL + SMALL COMMERCIAL ─────────────────────────────────────────
  {"type":"permit","trade":"ELECTRICAL","title":"ELECTRICAL - Panel upgrade 200A + EV charger install, single family","value":8_500,
   "addr":"4521 Mockingbird Ln, Dallas, TX 75205","owner":{"n":"Williams Family","p":"+12145553322","e":"j.williams@gmail.com"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(1),"src":"dallas-e7gq-4sah","score":58,
   "ai":{"project_type":"renovation","owner_type":"residential","key_materials":["200A panel","EV charger","conduit"]}},

  {"type":"permit","trade":"ROOFING","title":"ROOFING - Full tear-off and replace, 3,200 sqft residential + detached garage","value":22_500,
   "addr":"8814 Oak Cliff Blvd, Dallas, TX 75211","owner":{"n":"Martinez, Jose R","p":"+12145557788","e":"jmartinez@outlook.com"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(2),"src":"dallas-e7gq-4sah","score":63,
   "ai":{"project_type":"renovation","owner_type":"residential","sqft":3200,"key_materials":["shingles","ice barrier","ridge vent"]}},

  {"type":"permit","trade":"PLUMBING","title":"PLUMBING - Full bathroom remodel x3, kitchen reroute, water heater","value":35_000,
   "addr":"1122 Green Acres Dr, Nashville, TN 37211","owner":{"n":"Thompson, Mark & Sara","p":"+16155552244","e":"mthompson@icloud.com"},
   "gc":{"n":"Nashville Plumbing Pros","p":"+16155559900","lic":"TN-PLB-04412"},"status":"active","posted":d(3),"src":"nashville","score":67,
   "ai":{"project_type":"renovation","owner_type":"residential","key_materials":["PEX","tankless water heater","rough-in"]}},

  {"type":"permit","trade":"HVAC","title":"HVAC - New construction 4,800 sqft custom home, dual-zone system","value":48_000,
   "addr":"622 Hillside Dr, Austin, TX 78746","owner":{"n":"Chen, David & Lisa","p":"+15125551188","e":"dchen@techcorp.com"},
   "gc":{"n":"Austex Mechanical","p":"+15125554466","lic":"TX-HVAC-22341"},"status":"active","posted":d(4),"src":"austin-3syk-w9eu","score":71,
   "ai":{"project_type":"new_build","owner_type":"residential","sqft":4800,"key_materials":["2-zone heat pump","ERV","smart thermostat"]}},

  {"type":"permit","trade":"GENERAL","title":"GENERAL - Restaurant conversion 4,200 sqft retail to full commercial kitchen","value":285_000,
   "addr":"2244 N Milwaukee Ave, Chicago, IL 60647","owner":{"n":"Taqueria Moderna LLC","p":"+17735551234","e":"owner@taqueriamoderna.com"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(5),"src":"chicago-ydr8-5enu","score":72,
   "ai":{"project_type":"renovation","owner_type":"small_commercial","sqft":4200,"key_materials":["Type I hood","grease trap","commercial plumbing"]}},

  {"type":"permit","trade":"ELECTRICAL","title":"ELECTRICAL - Commercial solar array 150kW with net metering, brewery","value":165_000,
   "addr":"1901 River Rd, Louisville, KY 40206","owner":{"n":"Falls City Brewing Co","p":"+15025558800","e":"ops@fallscitybrewing.com"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(6),"src":"louisville","score":76,
   "ai":{"project_type":"new_build","owner_type":"small_commercial","key_materials":["solar panels","string inverters","net meter","conduit"]}},

  {"type":"permit","trade":"ROOFING","title":"ROOFING - Warehouse complex roof replacement 80,000 sqft, metal standing seam","value":640_000,
   "addr":"6500 Eastport Blvd, Indianapolis, IN 46219","owner":{"n":"Heartland Logistics LLC","p":"+13175558800","e":"facilities@heartlandlog.com"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(7),"src":"indianapolis","score":78,
   "ai":{"project_type":"renovation","owner_type":"small_commercial","sqft":80000,"key_materials":["standing seam metal","R-38 insulation"]}},

  {"type":"permit","trade":"PLUMBING","title":"PLUMBING - Apartment complex 96-unit re-pipe, copper to PEX","value":210_000,
   "addr":"3300 W Peoria Ave, Phoenix, AZ 85029","owner":{"n":"Desert Sun Apartments LLC","p":"+16025554400","e":"pm@desertsunaz.com"},
   "gc":{"n":"Arizona Plumbing Services","p":"+16025556600","lic":"AZ-ROC-C37-123456"},"status":"active","posted":d(8),"src":"phoenix","score":75,
   "ai":{"project_type":"renovation","owner_type":"small_commercial","units":96,"key_materials":["PEX-A","manifolds","water meter"]}},

  {"type":"permit","trade":"CONCRETE","title":"CONCRETE - Mixed-use development podium, 3 levels parking + 8 floors residential","value":9_800_000,
   "addr":"400 W 6th St, Austin, TX 78701","owner":{"n":"Capital City Urban LLC","p":"+15125557700","e":"projects@capitalcityurban.com"},
   "gc":{"n":"Swinerton Builders","p":"+15125559900","lic":"TX-GC-77741"},"status":"active","posted":d(9),"src":"austin-3syk-w9eu","score":92,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","units":185,"sqft":380000,"key_materials":["post-tension","precast","rebar","mat foundation"]}},

  {"type":"permit","trade":"HVAC","title":"HVAC - Full system replacement + duct cleaning 20-unit garden apartment","value":88_000,
   "addr":"1540 Maple Grove Dr, Charlotte, NC 28262","owner":{"n":"Maple Grove Properties","p":"+17045558800","e":""},"gc":{"n":"","p":"","lic":""},
   "status":"active","posted":d(10),"src":"charlotte","score":69,
   "ai":{"project_type":"renovation","owner_type":"small_commercial","units":20,"key_materials":["split systems","ductwork","thermostats"]}},

  {"type":"permit","trade":"ELECTRICAL","title":"ELECTRICAL - Tesla Powerwall fleet install + panel upgrades, 12 units","value":95_000,
   "addr":"7800 Congress Ave, Boca Raton, FL 33487","owner":{"n":"East Boca HOA","p":"+15615554400","e":"mgr@eastbocahoa.org"},
   "gc":{"n":"SunPower Electric FL","p":"+15615556600","lic":"FL-EC-13-001234"},"status":"active","posted":d(11),"src":"miami-dade","score":73,
   "ai":{"project_type":"renovation","owner_type":"small_commercial","units":12,"key_materials":["Powerwall","conduit","subpanel"]}},

  {"type":"permit","trade":"ROOFING","title":"ROOFING - K-8 school full roof replacement with green roof section","value":380_000,
   "addr":"2200 E Carson St, Pittsburgh, PA 15203","owner":{"n":"Pittsburgh USD","p":"+14125558800","e":"facilities@pps.k12.pa.us"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(12),"src":"pittsburgh","score":77,
   "ai":{"project_type":"renovation","owner_type":"institutional","sqft":42000,"key_materials":["EPDM","green roof growing medium","drain mat"]}},

  {"type":"permit","trade":"GENERAL","title":"GENERAL - Historic building adaptive reuse, 6-story loft conversion 60 units","value":7_200_000,
   "addr":"800 N Broadway, St. Louis, MO 63102","owner":{"n":"STL Urban Revitalization LLC","p":"+13145558800","e":"dev@stlurban.com"},
   "gc":{"n":"McCarthy Building Companies","p":"+13145556600","lic":"MO-GC-2023-0044"},"status":"active","posted":d(13),"src":"stlouis","score":87,
   "ai":{"project_type":"renovation","owner_type":"large_commercial","units":60,"sqft":95000,"key_materials":["structural steel","masonry restore","historic windows"]}},

  {"type":"permit","trade":"PLUMBING","title":"PLUMBING - Fire suppression + standpipe system, new 18-story office","value":520_000,
   "addr":"600 Travis St, Houston, TX 77002","owner":{"n":"Energy Corridor Partners","p":"+17135554422","e":""},
   "gc":{"n":"Western Mechanical","p":"+17135558800","lic":"TX-FP-5512"},"status":"active","posted":d(14),"src":"houston-djnh-at8a","score":80,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","sqft":220000,"key_materials":["dry pipe","wet pipe","standpipe","FDC"]}},

  {"type":"permit","trade":"ELECTRICAL","title":"ELECTRICAL - EV charging station network 40 Level 2 + 8 DCFC units, mall","value":480_000,
   "addr":"3000 Glendale Galleria, Glendale, CA 91210","owner":{"n":"Glendale Galleria LLC","p":"+18185559900","e":""},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(15),"src":"losangeles-yv23-pmwf","score":81,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","key_materials":["DCFC chargers","Level 2","switchgear","conduit"]}},

  {"type":"permit","trade":"HVAC","title":"HVAC - Brewery cold room expansion, walk-in cooler system 8,000 sqft","value":195_000,
   "addr":"900 Barley Dr, Denver, CO 80204","owner":{"n":"Mile High Brewing Co","p":"+13035558800","e":"ops@milehighbrewing.com"},
   "gc":{"n":"Colorado Refrigeration Inc","p":"+13035556644","lic":"CO-HVAC-8921"},"status":"active","posted":d(16),"src":"denver","score":71,
   "ai":{"project_type":"new_build","owner_type":"small_commercial","sqft":8000,"key_materials":["refrigeration compressor","evaporator","glycol loop"]}},

  {"type":"permit","trade":"CONCRETE","title":"CONCRETE - Bridge deck replacement, county infrastructure project","value":3_700_000,
   "addr":"US-290 at Loop 1, Austin, TX 78758","owner":{"n":"Travis County TxDOT","p":"+15125558800","e":""},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(17),"src":"austin-3syk-w9eu","score":83,
   "ai":{"project_type":"new_build","owner_type":"institutional","key_materials":["bridge deck concrete","rebar","form travelers"]}},

  {"type":"permit","trade":"ROOFING","title":"ROOFING - Airport terminal roof replacement + skylight system 200,000 sqft","value":4_600_000,
   "addr":"2400 Aviation Blvd, Nashville, TN 37214","owner":{"n":"Metropolitan Nashville Airport Authority","p":"+16155559900","e":""},
   "gc":{"n":"Gilbane Building Co","p":"+16155553300","lic":"TN-GC-15521"},"status":"active","posted":d(18),"src":"nashville","score":88,
   "ai":{"project_type":"renovation","owner_type":"institutional","sqft":200000,"key_materials":["EPDM","metal panel","structural skylight"]}},

  {"type":"permit","trade":"GENERAL","title":"GENERAL - Dental office buildout 3,800 sqft, full MEP + millwork","value":540_000,
   "addr":"6200 Sunset Dr, South Miami, FL 33143","owner":{"n":"Smile South Florida LLC","p":"+13055554400","e":"admin@smilesouthfl.com"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(19),"src":"miami-dade","score":66,
   "ai":{"project_type":"new_build","owner_type":"small_commercial","sqft":3800,"key_materials":["specialty plumbing","dental air","millwork"]}},

  {"type":"permit","trade":"ELECTRICAL","title":"ELECTRICAL - Multifamily 240-unit new construction, service entrance + units","value":1_800_000,
   "addr":"400 Biscayne Blvd, Miami, FL 33132","owner":{"n":"Biscayne Bay Developers","p":"+13055558800","e":""},
   "gc":{"n":"Suffolk Construction","p":"+13055553300","lic":"FL-CGC-029001"},"status":"active","posted":d(20),"src":"miami-dade","score":86,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","units":240,"sqft":275000,"key_materials":["service entrance","panels","wiring"]}},

  {"type":"permit","trade":"PLUMBING","title":"PLUMBING - Cannabis dispensary conversion, ADA upgrades + new plumbing","value":62_000,
   "addr":"1888 E McDowell Rd, Phoenix, AZ 85006","owner":{"n":"Desert Bloom Dispensary LLC","p":"+16025551122","e":""},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(21),"src":"phoenix","score":65,
   "ai":{"project_type":"renovation","owner_type":"small_commercial","sqft":2800,"key_materials":["ADA fixtures","backflow preventer","grease trap"]}},

  {"type":"permit","trade":"HVAC","title":"HVAC - Hospital NICU expansion HVAC, HEPA filtration + pressurization","value":2_200_000,
   "addr":"1001 W Broadway, Louisville, KY 40203","owner":{"n":"Baptist Health Louisville","p":"+15025588000","e":"facilities@baptisthealth.com"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(22),"src":"louisville","score":90,
   "ai":{"project_type":"new_build","owner_type":"institutional","key_materials":["HEPA","isolation rooms","constant volume AHU"]}},

  {"type":"permit","trade":"ROOFING","title":"ROOFING - 4 apartment buildings, storm damage replacement + upgrade","value":310_000,
   "addr":"6644 Fondren Rd, Houston, TX 77036","owner":{"n":"Fondren Properties LP","p":"+17135557722","e":"mgmt@fondrenprops.com"},
   "gc":{"n":"Gulf Coast Roofing","p":"+17135554411","lic":"TX-RC-32211"},"status":"active","posted":d(23),"src":"houston-djnh-at8a","score":70,
   "ai":{"project_type":"renovation","owner_type":"small_commercial","units":4,"sqft":32000,"key_materials":["shingles","ridge vent","decking"]}},

  {"type":"permit","trade":"CONCRETE","title":"CONCRETE - Luxury condo tower foundation, 52-story downtown Miami","value":18_000_000,
   "addr":"1000 Brickell Ave, Miami, FL 33131","owner":{"n":"Brickell Tower Developers","p":"+13055551100","e":"dev@brickelldev.com"},
   "gc":{"n":"Coastal Construction","p":"+13055558833","lic":"FL-CGC-1522"},"status":"active","posted":d(24),"src":"miami-dade","score":98,
   "ai":{"project_type":"new_build","owner_type":"large_commercial","units":320,"sqft":800000,"key_materials":["mat foundation","rebar","high-strength concrete"]}},

  {"type":"permit","trade":"ELECTRICAL","title":"ELECTRICAL - Community solar microgrid, 1.5MW + 4MWh storage, school district","value":2_900_000,
   "addr":"500 N Interstate 35, Round Rock, TX 78681","owner":{"n":"Round Rock ISD","p":"+15125554400","e":"facilities@roundrockisd.org"},
   "gc":{"n":"","p":"","lic":""},"status":"active","posted":d(25),"src":"austin-3syk-w9eu","score":91,
   "ai":{"project_type":"new_build","owner_type":"institutional","key_materials":["solar panels","battery storage","microgrid controller"]}},
]

CONTRACTORS = [
  {"name":"Turner Construction","trades":["GENERAL","CONCRETE","ELECTRICAL"],"licenses":[{"state":"IL","num":"IL-GC-00019","type":"General Contractor","exp":"2028-06-30","status":"ACTIVE"},{"state":"TX","num":"TX-GC-88801","type":"General Contractor","exp":"2028-06-30","status":"ACTIVE"}],"addr":"55 W Monroe St, Chicago, IL 60603","phone":"+13125558800","email":"bids@turnerconstruction.com","website":"turnerconstruction.com","permit_count":1847,"avg_project_value":4_200_000},
  {"name":"Skanska USA","trades":["GENERAL","CONCRETE","HVAC"],"licenses":[{"state":"TX","num":"TX-GC-88821","type":"General Contractor","exp":"2027-12-31","status":"ACTIVE"}],"addr":"5 Times Square, New York, NY 10036","phone":"+12125559900","email":"preconstruction@skanska.com","website":"skanska.com","permit_count":2100,"avg_project_value":8_500_000},
  {"name":"DPR Construction","trades":["GENERAL","CONCRETE"],"licenses":[{"state":"TX","num":"TX-GC-44321","type":"General Contractor","exp":"2027-09-30","status":"ACTIVE"}],"addr":"1450 Lake Robbins Dr, The Woodlands, TX 77380","phone":"+17135557700","email":"texas@dpr.com","website":"dpr.com","permit_count":890,"avg_project_value":6_100_000},
  {"name":"Lone Star HVAC","trades":["HVAC"],"licenses":[{"state":"TX","num":"TX-HVAC-22341","type":"HVAC Contractor","exp":"2027-06-30","status":"ACTIVE"}],"addr":"1100 Lamar St, Austin, TX 78701","phone":"+15125554444","email":"bids@lonestarhvac.com","website":"lonestarhvac.com","permit_count":287,"avg_project_value":125_000},
  {"name":"Gulf Coast Roofing","trades":["ROOFING"],"licenses":[{"state":"TX","num":"TX-RC-32211","type":"Roofing Contractor","exp":"2026-12-31","status":"ACTIVE"}],"addr":"9800 Harwin Dr, Houston, TX 77036","phone":"+17135554411","email":"bids@gulfcoastroofing.com","website":"gulfcoastroofing.com","permit_count":441,"avg_project_value":185_000},
  {"name":"Austin Plumbing Co","trades":["PLUMBING"],"licenses":[{"state":"TX","num":"TX-PLB-12345","type":"Master Plumber","exp":"2026-12-31","status":"ACTIVE"}],"addr":"2200 S Lamar Blvd, Austin, TX 78704","phone":"+15125550001","email":"dispatch@austinplumbing.com","website":"","permit_count":134,"avg_project_value":35_000},
  {"name":"Nashville Plumbing Pros","trades":["PLUMBING","FIRE_SUPPRESSION"],"licenses":[{"state":"TN","num":"TN-PLB-04412","type":"Master Plumber","exp":"2027-03-31","status":"ACTIVE"}],"addr":"400 Main St, Nashville, TN 37206","phone":"+16155559900","email":"office@nashvilleplumbing.com","website":"nashvilleplumbing.com","permit_count":198,"avg_project_value":48_000},
  {"name":"McKinstry","trades":["ELECTRICAL","HVAC","PLUMBING"],"licenses":[{"state":"WA","num":"WA-EC-91234","type":"Electrical Contractor","exp":"2027-08-31","status":"ACTIVE"}],"addr":"5005 3rd Ave S, Seattle, WA 98134","phone":"+12065552200","email":"national@mckinstry.com","website":"mckinstry.com","permit_count":756,"avg_project_value":890_000},
  {"name":"Coastal Construction FL","trades":["GENERAL","CONCRETE"],"licenses":[{"state":"FL","num":"FL-CGC-1522","type":"Certified General Contractor","exp":"2028-08-31","status":"ACTIVE"}],"addr":"8200 NW 33rd St, Doral, FL 33122","phone":"+13055558833","email":"estimating@coastalfl.com","website":"coastalconstruction.com","permit_count":512,"avg_project_value":12_000_000},
  {"name":"McCarthy Building Companies","trades":["GENERAL","CONCRETE"],"licenses":[{"state":"MO","num":"MO-GC-2023-0044","type":"General Contractor","exp":"2028-12-31","status":"ACTIVE"}],"addr":"1341 N Rock Hill Rd, St. Louis, MO 63124","phone":"+13145556600","email":"stlouis@mccarthy.com","website":"mccarthy.com","permit_count":1200,"avg_project_value":7_800_000},
]

def ts():
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

print("🌱 Seeding demo data...")
print(f"   {len(LEADS)} leads across all trades and cities")

for lead in LEADS:
    lead_id = generate_id(lead["src"], lead["title"][:60], lead.get("addr",""))
    lead["id"] = lead_id
    lead["keywords"] = extract_keywords(f"{lead['title']} {lead['trade']} {lead.get('addr','')}")
    lead["updated"] = ts()
    db.leads().document(lead_id).set(lead)

print(f"   {len(CONTRACTORS)} contractors (national + regional)")
for c in CONTRACTORS:
    cid = generate_id(c["name"], c["licenses"][0]["state"])
    c["id"] = cid
    c["updated"] = ts()
    db.contractors().document(cid).set(c)

print(f"\n✅ Demo database ready — {len(LEADS)} leads, {len(CONTRACTORS)} contractors")
print(f"   Value range: $8.5K → $18M")
print(f"   Cities: Chicago, Houston, Austin, Miami, Dallas, Nashville, DC, LA, Seattle, Phoenix, Denver, Atlanta")
print(f"   Trades: ELECTRICAL, HVAC, PLUMBING, ROOFING, CONCRETE, GENERAL")
print(f"   Types: federal bids + commercial + residential permits")
