import 'package:flutter/material.dart';

class BuildSubmitButton extends StatelessWidget {
  final VoidCallback onPressed;
  final String text; // إضافة هذا المتغير لاستقبال النص الخاص بالزر

  const BuildSubmitButton({
    super.key,
    required this.onPressed,
    required this.text, // تهيئة المتغير text هنا
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 15),
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          foregroundColor: Colors.white,
          backgroundColor: const Color.fromARGB(255, 47, 7, 226),
          shadowColor: Colors.black,
          elevation: 10,
          padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 15),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10.0),
          ),
        ),
        child: Text(
          text, // استخدم هنا النص الذي تم تمريره للزر
          style: const TextStyle(fontSize: 18),
        ),
      ),
    );
  }
}
