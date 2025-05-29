import 'package:flutter/material.dart';

class BuildInputRow extends StatelessWidget {
  final String label;
  final IconData icon;
  final double spacing;

  const BuildInputRow({
    super.key,
    required this.label,
    required this.icon,
    required this.spacing,
    required Null Function(dynamic value) onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const SizedBox(width: 20),
        Text(
          label,
          style: const TextStyle(fontSize: 20),
        ),
        SizedBox(width: spacing),
        Expanded(
          child: TextField(
            decoration: InputDecoration(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(30.0),
                borderSide: const BorderSide(color: Colors.black),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(30.0),
                borderSide: const BorderSide(color: Colors.black, width: 2),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(30.0),
                borderSide: const BorderSide(color: Colors.blue, width: 2),
              ),
            ),
          ),
        ),
        const SizedBox(width: 15),
        Padding(
          padding: const EdgeInsets.only(right: 10),
          child: Icon(
            icon,
            size: 50,
            color: Colors.black,
          ),
        ),
      ],
    );
  }
}
