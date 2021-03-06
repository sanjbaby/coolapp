from flask import *
import os.path
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename
import pyodbc
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import pyaudio
import wave
import time
import requests
import os

"""# Constants for IBM COS values
COS_ENDPOINT = "https://s3.us-south.objectstorage.softlayer.net"  # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "_bAzHuCAN1yPz4Rcg5CZY1Tbp0UOpshuMhpoNkIvJAa3"  # eg "W00YiRnLW4a3fTjHB-oiB-2ySfTrFBIQQWanc--P3byk"
COS_AUTH_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"
COS_RESOURCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/693fe8ead49b44b192004113d21b15c2:fce26086-5b77-42cc-b1aa-d388aa2853d7::"

# Create resource
cos = ibm_boto3.resource("s3",
                         ibm_api_key_id=COS_API_KEY_ID,
                         ibm_service_instance_id=COS_RESOURCE_CRN,
                         ibm_auth_endpoint=COS_AUTH_ENDPOINT,
                         config=Config(signature_version="oauth"),
                         endpoint_url=COS_ENDPOINT
                         )

print("Retrieving bucket contents from: {0}".format("gamification-cos-standard-tkq"))
try:
    files = cos.Bucket("gamification-cos-standard-tkq").objects.all()
    for file in files:
        print("Item: {0} ({1} bytes).".format(file.key, file.size))

        if os.path.isfile('static/uploads/'+file.key):
            print("File exist")
        else:
            print("File not exist")
            cos.Bucket('gamification-cos-standard-tkq').download_file(file.key,
                                                                  'static/uploads/'+file.key)

except ClientError as be:
    print("CLIENT ERROR: {0}\n".format(be))
except Exception as e:
    print("Unable to retrieve bucket contents: {0}".format(e))
"""
server = 'tcp:bluepanther1.database.windows.net'
database = 'blue'
username = 'coolapp'
password = 'cool@app1234'

app = Flask(__name__)
app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def getLoginDetails():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
        else:
            loggedIn = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = '" + session['email'] + "'")
            userId, firstName = cur.fetchone()
            cur.execute("SELECT count(productId) FROM kart WHERE userId = " + str(userId))
            noOfItems = cur.fetchone()[0]
    conn.close()
    return (True, 'All User', 0)


@app.route("/")
def root():
    loggedIn, firstName, noOfItems = getLoginDetails()
    cnxn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)

    cursor = cnxn.cursor()
    cursor.execute('select distinct(family_name) from coolapp.XXIBM_PRODUCT_CATALOG')
    categoryData = [x[0] for x in cursor.fetchall()]
    list_ctg = []
    cursor.execute(
        'select PP.Item_Number,PS.Desc_ription,pp.List_Price,PS.Long_Description, CONCAT(PP.Item_Number,\'.jpg\') as img,pp.InStock from coolapp.XXIBM_PRODUCT_STYLE PS inner join coolapp.XXIBM_PRODUCT_PRICING PP on PS.item_number+1 = PP.Item_Number')
    for row in cursor.fetchall():
        # print(row)
        row = list(row)
        list_ctg.append(row)
    itemData = parse(list_ctg)

    cnxn.close()
    return render_template('home.html', itemData=itemData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems,
                           categoryData=categoryData)


@app.route('/searchop', methods=['GET', 'POST'])
def result():
    loggedIn, firstName, noOfItems = getLoginDetails()
    if request.method == 'POST':
        result = request.form
        # print(result, "Hi From Result")
        result = result['searchQuery']
        raw_result=result
        result = result.upper()
        result = "\'%" + str(result) + "%\'"
        # print(result,"actual result")

    list_ctg = []
    cnxn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)

    cursor = cnxn.cursor()
    cursor.execute(
        "select  PSKU.Item_Number,PSKU.Desc_ription,PP.List_Price,CONCAT(PP.Item_Number,'.jpg') as img, PC.Family_Name,psku.SKUAtt_Value1,psku.SKUAtt_Value2 from coolapp.XXIBM_PRODUCT_CATALOG PC inner join coolapp.XXIBM_PRODUCT_SKU PSKU on PC.Commodity = PSKU.Catalogue_Category inner join coolapp.XXIBM_PRODUCT_PRICING PP on PSKU.Item_Number = PP.Item_Number where upper(PSKU.Desc_ription) like" + result + "or upper(PSKU.Long_Description) like" + result)
    for row in cursor.fetchall():
        # print(row)
        row = list(row)
        list_ctg.append(row)
    cnxn.close()
    if (len(list_ctg)) == 0:
        return render_template('No_Data.html',searchtext=raw_result)

    else:
        categoryName = list_ctg[0][4]
        data = parse(list_ctg)

        return render_template('searchop.html', data=data, loggedIn=loggedIn, firstName=firstName,
                               noOfItems=noOfItems, categoryName=categoryName)


@app.route('/searchvoice', methods=['GET', 'POST'])
def voicesearch():
    loggedIn, firstName, noOfItems = getLoginDetails()
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    CHUNK = 1024
    RECORD_SECONDS = 4
    time1 = time.strftime("%Y%m%d-%H%M%S")
    WAVE_OUTPUT_FILENAME = time1 + "file.wav"

    audio = pyaudio.PyAudio()

    # start Recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    print("recording...")
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("finished recording")

    # stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()

    waveFile = wave.open('static/uploads/' + WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    url = 'https://gateway-lon.watsonplatform.net/speech-to-text/api/v1/recognize'
    headers = {'Content-Type': 'audio/wav'}
    data = open('static/uploads/' + WAVE_OUTPUT_FILENAME, 'rb').read()
    try:
        response = requests.post(
            'https://api.us-south.speech-to-text.test.watson.cloud.ibm.com/instances/b20b578f-60a7-4e72-a3b6-08f691ff9b3b/v1/recognize',
            headers=headers,
            data=data, auth=('apikey', 'TItad1CugTOubrsb2zXaOhswr7XB_RJvYRMn_E4hQDRO'))
    except:
        print("exception")
    new_value = response.json()
    new_value = new_value['results']
    print(len(new_value))
    if len(new_value) != 0:
        voice_text = new_value[0]['alternatives'][0]['transcript']
        raw_voice_text=voice_text
        voice_text = voice_text.upper()
        voice_text = "\'%" + str(voice_text) + "%\'"
        print(new_value)
        print(voice_text)
        print(type(voice_text))
    else:
        voice_text = '\'%Bad-Voice-Search%\''
        raw_voice_text = 'Bad voice Search'
    # print(new_value[0]['alternatives'][0]['transcript'])
    os.remove('static/uploads/' + WAVE_OUTPUT_FILENAME)

    if request.method == 'POST':
        result = request.form
    # print(result, "Hi From Result")
        result = result['searchQuery']
        result = result.upper()
        result = "\'%" + str(result) + "%\'"
    # print(result,"actual result")

    list_ctg = []
    cnxn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)

    cursor = cnxn.cursor()
    cursor.execute(
        "select  PSKU.Item_Number,PSKU.Desc_ription,PP.List_Price,CONCAT(PP.Item_Number,'.jpg') as img, PC.Family_Name,psku.SKUAtt_Value1,psku.SKUAtt_Value2 from coolapp.XXIBM_PRODUCT_CATALOG PC inner join coolapp.XXIBM_PRODUCT_SKU PSKU on PC.Commodity = PSKU.Catalogue_Category inner join coolapp.XXIBM_PRODUCT_PRICING PP on PSKU.Item_Number = PP.Item_Number where upper(PSKU.Desc_ription) like" + voice_text + "or upper(PSKU.Long_Description) like" + voice_text)
    # cursor.execute("select  PSKU.Item_Number,PSKU.Desc_ription,PP.List_Price,CONCAT(PP.Item_Number,'.jpg') as img, PC.Family_Name,psku.SKUAtt_Value1,psku.SKUAtt_Value2 from coolapp.XXIBM_PRODUCT_CATALOG PC inner join coolapp.XXIBM_PRODUCT_SKU PSKU on PC.Commodity = PSKU.Catalogue_Category inner join coolapp.XXIBM_PRODUCT_PRICING PP on PSKU.Item_Number = PP.Item_Number where upper(PSKU.Desc_ription) like \'%SUIT%\'")
    # print(result, "Hi From after cursor")
    for row in cursor.fetchall():
    # print(row)
        row = list(row)
        list_ctg.append(row)
    cnxn.close()
    if (len(list_ctg)) == 0:
        return render_template('No_Data.html',searchtext=raw_voice_text)

    else:
        categoryName = list_ctg[0][4]
        data = parse(list_ctg)

    return render_template('searchvoice.html', data=data, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems, categoryName=categoryName, voice_text=raw_voice_text)


@app.route("/add")
def admin():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT categoryId, name FROM categories")
        categories = cur.fetchall()
    conn.close()
    return render_template('add.html', categories=categories)


@app.route("/addItem", methods=["GET", "POST"])
def addItem():
    if request.method == "POST":
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        categoryId = int(request.form['category'])

        # Uploading image procedure
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        imagename = filename
        with sqlite3.connect('database.db') as conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    '''INSERT INTO products (name, price, description, image, stock, categoryId) VALUES (?, ?, ?, ?, ?, ?)''',
                    (name, price, description, imagename, stock, categoryId))
                conn.commit()
                msg = "added successfully"
            except:
                msg = "error occured"
                conn.rollback()
        conn.close()
        print(msg)
        return redirect(url_for('root'))


@app.route("/displayCategory")
def displayCategory():
    loggedIn, firstName, noOfItems = getLoginDetails()
    categoryId = request.args.get("categoryId")
    print(categoryId)
    if categoryId == 'C':
        categoryId = '\'Clothing\''
    elif categoryId == 'F':
        categoryId = '\'Footwear\''
    elif categoryId == 'L':
        categoryId = '\'Luggage and handbags and packs and cases\''
    elif categoryId == 'P':
        categoryId = '\'Personal care products\''
    elif categoryId == 'S':
        categoryId = '\'Sewing supplies and accessories\''
    else:

        categoryId = '\'Clothing\''
    print(categoryId)
    list_ctg = []
    cnxn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)

    cursor = cnxn.cursor()
    cursor.execute(
        "select  PSKU.Item_Number,PSKU.Desc_ription,PP.List_Price,CONCAT(PP.Item_Number,'.jpg') as img, PC.Family_Name,psku.SKUAtt_Value1,psku.SKUAtt_Value2 from coolapp.XXIBM_PRODUCT_CATALOG PC inner join coolapp.XXIBM_PRODUCT_SKU PSKU on PC.Commodity = PSKU.Catalogue_Category inner join coolapp.XXIBM_PRODUCT_PRICING PP on PSKU.Item_Number = PP.Item_Number where PC.family_name = " + categoryId)  # \'Clothing\'")
    for row in cursor.fetchall():
        # print(row)
        row = list(row)
        list_ctg.append(row)
    cnxn.close()
    if (len(list_ctg)) == 0:
        return render_template('No_Data.html')

    else:
        categoryName = list_ctg[0][4]
        data = parse(list_ctg)

        return render_template('displayCategory.html', data=data, loggedIn=loggedIn, firstName=firstName,
                               noOfItems=noOfItems, categoryName=categoryName)


@app.route("/account/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    return render_template("profileHome.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)


@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE email = '" +
            session['email'] + "'")
        profileData = cur.fetchone()
    conn.close()
    return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems)


@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId, password FROM users WHERE email = '" + session['email'] + "'")
            userId, password = cur.fetchone()
            if (password == oldPassword):
                try:
                    cur.execute("UPDATE users SET password = ? WHERE userId = ?", (newPassword, userId))
                    conn.commit()
                    msg = "Changed successfully"
                except:
                    conn.rollback()
                    msg = "Failed"
                return render_template("changePassword.html", msg=msg)
            else:
                msg = "Wrong password"
        conn.close()
        return render_template("changePassword.html", msg=msg)
    else:
        return render_template("changePassword.html")


@app.route("/updateProfile", methods=["GET", "POST"])
def updateProfile():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        with sqlite3.connect('database.db') as con:
            try:
                cur = con.cursor()
                cur.execute(
                    'UPDATE users SET firstName = ?, lastName = ?, address1 = ?, address2 = ?, zipcode = ?, city = ?, state = ?, country = ?, phone = ? WHERE email = ?',
                    (firstName, lastName, address1, address2, zipcode, city, state, country, phone, email))

                con.commit()
                msg = "Saved Successfully"
            except:
                con.rollback()
                msg = "Error occured"
        con.close()
        return redirect(url_for('editProfile'))


@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('login.html', error=error)


@app.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    productId = request.args.get('productId')
    print(productId)
    cnxn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)

    cursor = cnxn.cursor()
    cursor.execute(
        "select PSKU.Item_Number,PSKU.Desc_ription,PP.list_price,CONCAT(PP.Item_Number,\'.jpg\') as image,pp.InStock from coolapp.XXIBM_PRODUCT_SKU PSKU inner join coolapp.XXIBM_PRODUCT_PRICING PP on PP.Item_Number=PSKU.Item_Number where PSKU.Item_Number = " + productId)  # \'Clothing\'")
    productData = cursor.fetchone()
    cnxn.close()
    return render_template("productDescription.html", data=productData, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems)


@app.route("/addToCart")
def addToCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        productId = int(request.args.get('productId'))
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = '" + session['email'] + "'")
            userId = cur.fetchone()[0]
            try:
                cur.execute("INSERT INTO kart (userId, productId) VALUES (?, ?)", (userId, productId))
                conn.commit()
                msg = "Added successfully"
            except:
                conn.rollback()
                msg = "Error occured"
        conn.close()
        return redirect(url_for('root'))


@app.route("/cart")
def cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute(
            "SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = " + str(
                userId))
        products = cur.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
    return render_template("cart.html", products=products, totalPrice=totalPrice, loggedIn=loggedIn,
                           firstName=firstName, noOfItems=noOfItems)


@app.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    productId = int(request.args.get('productId'))
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        try:
            cur.execute("DELETE FROM kart WHERE userId = " + str(userId) + " AND productId = " + str(productId))
            conn.commit()
            msg = "removed successfully"
        except:
            conn.rollback()
            msg = "error occured"
    conn.close()
    return redirect(url_for('root'))


@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))


def is_valid(email, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False


@app.route("/checkout", methods=['GET', 'POST'])
def payment():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']

    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute(
            "SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = " + str(
                userId))
        products = cur.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
        print(row)
        cur.execute("INSERT INTO Orders (userId, productId) VALUES (?, ?)", (userId, row[0]))
    cur.execute("DELETE FROM kart WHERE userId = " + str(userId))
    conn.commit()

    return render_template("checkout.html", products=products, totalPrice=totalPrice, loggedIn=loggedIn,
                           firstName=firstName, noOfItems=noOfItems)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Parse form data
        password = request.form['password']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']

        with sqlite3.connect('database.db') as con:
            try:
                cur = con.cursor()
                cur.execute(
                    'INSERT INTO users (password, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (
                    hashlib.md5(password.encode()).hexdigest(), email, firstName, lastName, address1, address2, zipcode,
                    city, state, country, phone))

                con.commit()

                msg = "Registered Successfully"
            except:
                con.rollback()
                msg = "Error occured"
        con.close()
        return render_template("login.html", error=msg)


@app.route("/registerationForm")
def registrationForm():
    return render_template("register.html")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
