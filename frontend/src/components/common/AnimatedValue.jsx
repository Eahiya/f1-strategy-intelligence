import React, { useEffect, useRef } from 'react';
import { animate } from 'framer-motion';

/**
 * AnimatedValue Component
 * Smoothly animates number changes to prevent layout "jumping" 
 * and provide a premium telemetry feel.
 */
const AnimatedValue = ({ 
  value, 
  precision = 2, 
  prefix = '', 
  suffix = '', 
  className = '',
  duration = 0.5 
}) => {
  const nodeRef = useRef();

  useEffect(() => {
    const node = nodeRef.current;
    if (!node) return;

    const startValue = parseFloat(node.textContent.replace(/[^\d.-]/g, '') || 0);
    const endValue = typeof value === 'string' ? parseFloat(value) : value;

    if (typeof endValue !== 'number' || isNaN(endValue)) {
      node.textContent = `${prefix}${value}${suffix}`;
      return;
    }

    const controls = animate(startValue, endValue, {
      duration: duration,
      onUpdate(v) {
        if (typeof v === 'number') {
          node.textContent = `${prefix}${v.toFixed(precision)}${suffix}`;
        } else {
          node.textContent = `${prefix}${v}${suffix}`;
        }
      },
    });

    return () => controls.stop();
  }, [value, precision, prefix, suffix, duration]);

  return (
    <span ref={nodeRef} className={className}>
      {prefix}{parseFloat(value).toFixed(precision)}{suffix}
    </span>
  );
};

export default AnimatedValue;
