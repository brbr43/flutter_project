import 'package:campoundnew/admin_pages/Complaint.dart';
import 'package:campoundnew/admin_pages/Organize_a_party.dart';
import 'package:campoundnew/admin_pages/SendNotification%20.dart';
import 'package:campoundnew/admin_pages/Tennis_organization.dart';
import 'package:campoundnew/admin_pages/Yoga_organization.dart';
import 'package:campoundnew/admin_pages/users.dart';
import 'package:flutter/material.dart';

class HomeScreenAdmin extends StatelessWidget {
  const HomeScreenAdmin({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(
            Icons.arrow_back,
            color: Colors.white,
            size: 40,
          ),
          onPressed: () {},
        ),
        title: const Center(
          child: Text(
            'Welcome',
            style: TextStyle(
              fontSize: 20,
              color: Colors.white,
              fontFamily: 'Pacifico',
            ),
          ),
        ),
        backgroundColor: const Color.fromARGB(25, 47, 7, 226),
      ),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 10.0),
        child: Align(
          alignment: Alignment.topCenter,
          child: Container(
            padding: const EdgeInsets.all(20.0),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20.0),
              border: Border.all(
                color: const Color.fromARGB(255, 47, 7, 226),
                width: 3,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  spreadRadius: 5,
                  blurRadius: 15,
                  offset: const Offset(0, 3),
                ),
              ],
            ),
            child: SingleChildScrollView(
              // Make the container scrollable
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Choose an Activity ',
                    style: TextStyle(
                      fontSize: 24,
                      color: Color.fromARGB(255, 47, 7, 226),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 20),
                  GridView.count(
                    crossAxisCount: 3,
                    shrinkWrap: true,
                    mainAxisSpacing: 20,
                    crossAxisSpacing: 20,
                    physics: const NeverScrollableScrollPhysics(),
                    children: [
                      _buildIconWithLabel(
                          Icons.sports_tennis_outlined, 'Tennis', () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const TennisOrganization(),
                          ),
                        );
                      }),
                      _buildIconWithLabel(Icons.self_improvement, 'private gym',
                          () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const YogaOrganization(),
                          ),
                        );
                      }),
                      _buildIconWithLabel(Icons.celebration, 'Party', () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const OrganizeAParty(),
                          ),
                        );
                      }),
                      _buildIconWithLabel(
                          Icons.notification_add, 'Seend Notification', () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const SendNotification(),
                          ),
                        );
                      }),
                      _buildIconWithLabel(Icons.person, 'show users', () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const Users(),
                          ),
                        );
                      }),
                      _buildIconWithLabel(
                          Icons.report_problem_sharp, 'show Complaints', () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ComplaintPage(),
                          ),
                        );
                      }),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

Widget _buildIconWithLabel(
    IconData icon, String label, VoidCallback onPressed) {
  return InkWell(
    onTap: onPressed,
    borderRadius: BorderRadius.circular(10),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          icon,
          size: 40,
          color: const Color.fromARGB(255, 47, 7, 226),
        ),
        const SizedBox(height: 5),
        Text(
          label,
          style: const TextStyle(fontSize: 14, color: Colors.black),
          textAlign: TextAlign.center,
        ),
      ],
    ),
  );
}
