# AWS Cloud PC Setup Guide (Phone-Friendly)

Follow these steps on your phone/PC to get your **Nifty Theta Sniper** running 24/7 in the cloud for free.

### **Step 1: Create your AWS Account**
1.  Go to [aws.amazon.com](https://aws.amazon.com/) and click **"Create an AWS Account"**.
2.  Follow the sign-up (you will need a Credit/Debit card for the ₹2 verification charge, which is refunded).
3.  Choose the **"Free Tier"** plan.

### **Step 2: Launch your "Trading PC"**
1.  In the AWS Console, search for **"EC2"**.
2.  Change your region (Top Right) to **Mumbai (ap-south-1)**. 🚀 *Crucial for NSE speed.*
3.  Click **"Launch Instance"**.
4.  **Name**: `ThetaSniper_VPS`.
5.  **OS**: Select **"Microsoft Windows Server 2022"** (Recommended for 1GB RAM efficiency).
    *Note: While 2025 is available, it is heavier and may crash on the 1GB Free Tier instance.*
6.  **Instance Type**: Select **"t3.micro"** (This is the standard Free Tier choice in 2026).
    *Note: If t3.micro is not available, look for any instance marked "Free tier eligible".*
7.  **Key Pair**: Create a new key pair, name it `my_trading_key`, and download the `.pem` file.

### **Step 3: Connect from your Phone**
1.  Download **"Microsoft Remote Desktop"** (RD Client) from the Play Store or App Store.
2.  In EC2, click your instance and click **"Connect"** → **"RDP Client"**.
3.  **Public DNS**: Copy this address.
4.  **Username**: `Administrator`.
5.  **Password**: Click "Get Password" (upload your `.pem` file to see it).
6.  Open the RD Client app on your phone, add a new PC, paste the DNS, and enter your credentials.

---

### **Step 4: One-Click Setup (Inside the VPS)**
Once you are inside your Cloud PC, I have prepared a **Setup Script** for you. Just copy your `nifty_theta_sniper` folder there and run:
`setup_vps.bat` (I am creating this for you now).

**Ready to get your AWS account started? Just say "Got my AWS" when you're done with Step 1.**
