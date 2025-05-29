import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:campoundnew/api/ApiService.dart';
import 'package:campoundnew/model/ProfileModel.dart';
import 'package:campoundnew/auth/AuthCubit.dart';

class ProfileScreen extends StatefulWidget {
  @override
  _ProfileScreenState createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late Future<ProfileModel?> profileFuture =
      Future.value(null); // Initialize with null

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    String? token = await context.read<AuthCubit>().getStoredToken();
    if (token != null) {
      setState(() {
        profileFuture = ApiService().fetchProfile(token);
      });
    } else {
      print("❌ Token not found!");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[200], // Light background color
      appBar: AppBar(
        title: Text("Profile"),
        centerTitle: true,
        backgroundColor: const Color.fromARGB(255, 47, 7, 226),
      ),
      body: FutureBuilder<ProfileModel?>(
        future: profileFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError || snapshot.data == null) {
            return Center(child: Text("❌ Failed to load data"));
          }

          ProfileModel profile = snapshot.data!;

          return SingleChildScrollView(
            padding: EdgeInsets.all(16.0),
            child: Column(
              children: [
                // Circular avatar with a user icon
                CircleAvatar(
                  radius: 50,
                  backgroundImage: AssetImage(
                      "assets/images/test.webp"), // Replace with your custom image
                  backgroundColor: Colors.grey[300],
                ),
                SizedBox(height: 16),

                // Data card
                Card(
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                  elevation: 4,
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Column(
                      children: [
                        _buildProfileRow(Icons.email, "Email", profile.email),
                        _buildProfileRow(
                            Icons.phone, "Phone Number", profile.phoneNumber),
                        _buildProfileRow(Icons.home, "Apartment Number",
                            profile.apartmentNumber.toString()),
                        _buildProfileRow(Icons.location_city, "Compound",
                            profile.complexName),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  // Reusable widget for information rows
  Widget _buildProfileRow(IconData icon, String title, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        children: [
          Icon(icon, color: const Color.fromARGB(255, 47, 7, 226), size: 28),
          SizedBox(width: 12),
          Text("$title:",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          SizedBox(width: 8),
          Expanded(
            child: Text(value,
                style: TextStyle(fontSize: 16),
                overflow: TextOverflow.ellipsis),
          ),
        ],
      ),
    );
  }
}
