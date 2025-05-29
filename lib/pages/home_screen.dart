import 'package:campoundnew/pages/Yoga.dart';
import 'package:campoundnew/pages/activti.dart';
import 'package:campoundnew/pages/help.dart';
import 'package:campoundnew/pages/party.dart';
import 'package:campoundnew/pages/profiel.dart';
import 'package:campoundnew/pages/tennis.dart';
import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

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
        backgroundColor: const Color.fromARGB(255, 47, 7, 226),
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
                            builder: (context) => Tennis(),
                          ),
                        );
                      }),
                      _buildIconWithLabel(Icons.self_improvement, 'private gym',
                          () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => Yoga(),
                          ),
                        );
                      }),
                      _buildIconWithLabel(Icons.celebration, 'Party', () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => Party(),
                          ),
                        );
                      }),
                      _buildIconWithLabel(Icons.help, 'Help', () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const Help(),
                          ),
                        );
                      }),
                      _buildIconWithLabel(Icons.history, 'activity', () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => Activity(),
                          ),
                        );
                      }),
                      _buildIconWithLabel(Icons.person_pin, 'profiel', () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => ProfileScreen(),
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
}
