import 'package:campoundnew/api/HelpBooking.dart';
import 'package:campoundnew/auth/AuthCubit.dart';
import 'package:campoundnew/widget/buildSubmitButton.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class Help extends StatefulWidget {
  const Help({super.key});

  @override
  State<Help> createState() => _HelpState();
}

class _HelpState extends State<Help> {
  String? masseghelp; // متغير لتخزين النص المدخل
  final TextEditingController _controller =
      TextEditingController(); // Controller للتحكم في النص

  @override
  Widget build(BuildContext context) {
    final Helpbooking api = Helpbooking(); // استخدام الكلاس الجديد
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
            'Help',
            style: TextStyle(
              fontSize: 20,
              color: Colors.white,
              fontFamily: 'Pacifico',
            ),
          ),
        ),
        backgroundColor: const Color.fromARGB(255, 47, 7, 226),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                '"If you have a problem, write it below."',
                style: TextStyle(fontSize: 18),
              ),
              const SizedBox(height: 20),
              // TextField لتخزين النص المدخل
              TextField(
                controller: _controller, // ربط الcontroller مع النص
                maxLines: 5, // Allows multiple lines for input
                decoration: InputDecoration(
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10.0),
                    borderSide: const BorderSide(color: Colors.black),
                  ),
                  hintText: 'Write your problem here.....',
                  hintStyle: const TextStyle(color: Colors.grey),
                ),
                onChanged: (value) {
                  setState(() {
                    masseghelp = value; // تخزين النص المدخل
                  });
                },
              ),
              const SizedBox(height: 20),
              Center(
                child: BuildSubmitButton(
                  onPressed: () async {
                    if (masseghelp != null && masseghelp!.isNotEmpty) {
                      final token =
                          await context.read<AuthCubit>().getStoredToken();
                      // إرسال الرسالة مع التوكن
                      await api.addBooking(masseghelp!, token!);

                      // إفراغ النص بعد الإرسال
                      setState(() {
                        masseghelp = null;
                        _controller.clear(); // مسح النص من TextField
                      });

                      // إظهار رسالة نجاح مع لون أخضر
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: const Text(
                              'The problem has been submitted successfully.'),
                          backgroundColor: Colors.green, // تعيين اللون الأخضر
                        ),
                      );
                    } else {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Please write the problem.'),
                          backgroundColor:
                              Colors.red, // اللون الأحمر عند وجود خطأ
                        ),
                      );
                    }
                  },
                  text: 'Send', // تصحيح النص من 'sned' إلى 'Send'
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
