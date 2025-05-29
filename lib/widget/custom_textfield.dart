import 'package:flutter/material.dart';

// ignore: must_be_immutable
class CustomTextfield extends StatelessWidget {
  String? text2;
  VoidCallback? onTab;

  CustomTextfield(
      {Key? key,
      this.onTab,
      this.text2,
      required Null Function(dynamic data) onChanged})
      : super(key: key);
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTab,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(8.0),
          child: Container(
            height: 40,
            width: double.infinity,
            decoration: BoxDecoration(
                color: const Color.fromARGB(255, 255, 255, 255),
                borderRadius: BorderRadius.circular(10)),
            child: Center(
              child: Text(
                '$text2',
                style: const TextStyle(
                  color: Color.fromARGB(255, 55, 53, 138),
                  fontSize: 20,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
