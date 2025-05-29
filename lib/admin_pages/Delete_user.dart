import 'package:flutter/material.dart';

class DeleteUser extends StatelessWidget {
  const DeleteUser({super.key});

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
          onPressed: () {
            Navigator.pop(context); // Return to the previous page
          },
        ),
        title: const Center(
          child: Text(
            'DeleteUser',
            style: TextStyle(
              fontSize: 20,
              color: Colors.white,
              fontFamily: 'Pacifico',
            ),
          ),
        ),
        backgroundColor: const Color.fromARGB(255, 47, 7, 226),
      ),
    );
  }
}
