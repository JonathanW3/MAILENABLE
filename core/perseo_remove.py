#!/usr/bin/env python3
"""
Eliminador de Logo PERSEO WEB de documentos PDF
Detecta y elimina el logo independientemente del número de páginas
"""

import fitz  # PyMuPDF
import os
import sys
from typing import List, Tuple, Optional
import re
import io

class PerseoLogoRemover:
    def __init__(self):
        # Patrones de texto que pueden indicar la presencia del logo PERSEO
        self.perseo_patterns = [
            r"PERSEO",
            r"perseo",
            r"Perseo",
            r"PERSEO\s*WEB",
            r"perseo\s*web"
        ]
        
        # Área típica donde suele aparecer el logo (parte superior de la página)
        # Estos valores se pueden ajustar según sea necesario
        self.logo_search_area = {
            'bottom_margin': 100,  # Píxeles desde abajo donde buscar el logo
            'left_margin': 50,     # Píxeles desde la izquierda
            'right_margin': 50,    # Píxeles desde la derecha
        }
    
    def detect_perseo_elements(self, page) -> List[dict]:
        """
        Detecta elementos relacionados con PERSEO en una página
        """
        found_elements = []
        
        # Buscar texto relacionado con PERSEO en toda la página
        text_instances = page.search_for("PERSEO")
        text_instances.extend(page.search_for("Perseo"))
        text_instances.extend(page.search_for("perseo"))
        
        # Filtrar solo el texto que está en el pie de página
        page_rect = page.rect
        bottom_area_y = page_rect.height - self.logo_search_area['bottom_margin']
        
        for rect in text_instances:
            # Solo incluir texto que esté en la parte inferior de la página
            if rect.y0 >= bottom_area_y:
                found_elements.append({
                    'type': 'text',
                    'rect': rect,
                    'description': f'Texto PERSEO en pie de página {rect}'
                })
            else:
                print(f"  ⚠ Texto PERSEO encontrado fuera del pie de página (ignorado): {rect}")
        
        # Buscar imágenes en el área inferior (pie de página)
        page_rect = page.rect
        search_rect = fitz.Rect(
            self.logo_search_area['left_margin'],
            page_rect.height - self.logo_search_area['bottom_margin'],  # Desde abajo hacia arriba
            page_rect.width - self.logo_search_area['right_margin'],
            page_rect.height  # Hasta el final de la página
        )
        
        # Obtener todas las imágenes de la página
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            # Obtener información de la imagen
            img_rect = page.get_image_bbox(img[7])  # img[7] es el xref de la imagen
            
            # Verificar si la imagen está en el área de búsqueda (pie de página)
            if self._rect_intersects(img_rect, search_rect):
                found_elements.append({
                    'type': 'image',
                    'rect': img_rect,
                    'xref': img[7],
                    'description': f'Imagen en pie de página {img_rect}'
                })
        
        return found_elements
    
    def _rect_intersects(self, rect1: fitz.Rect, rect2: fitz.Rect) -> bool:
        """Verifica si dos rectángulos se intersectan"""
        return not (rect1.x1 < rect2.x0 or rect2.x1 < rect1.x0 or 
                   rect1.y1 < rect2.y0 or rect2.y1 < rect1.y0)
    
    def remove_perseo_elements(self, page, elements: List[dict]) -> int:
        """
        Elimina los elementos de PERSEO de una página
        """
        removed_count = 0
        
        for element in elements:
            try:
                if element['type'] == 'text':
                    # Para texto, creamos un rectángulo blanco que lo cubra
                    rect = element['rect']
                    # Expandir ligeramente el rectángulo para asegurar cobertura completa
                    expanded_rect = fitz.Rect(
                        rect.x0 - 2, rect.y0 - 2,
                        rect.x1 + 2, rect.y1 + 2
                    )
                    
                    # Dibujar rectángulo blanco sobre el texto
                    page.draw_rect(expanded_rect, color=(1, 1, 1), fill=(1, 1, 1))
                    removed_count += 1
                    print(f"  ✓ Eliminado texto PERSEO en {rect}")
                
                elif element['type'] == 'image':
                    # Para imágenes, intentamos eliminarlas o cubrirlas
                    rect = element['rect']
                    
                    # Primero intentar eliminar la imagen por referencia
                    try:
                        # Nota: La eliminación directa de imágenes puede ser compleja
                        # Como alternativa, cubrimos la imagen con un rectángulo blanco
                        expanded_rect = fitz.Rect(
                            rect.x0 - 1, rect.y0 - 1,
                            rect.x1 + 1, rect.y1 + 1
                        )
                        page.draw_rect(expanded_rect, color=(1, 1, 1), fill=(1, 1, 1))
                        removed_count += 1
                        print(f"  ✓ Cubierta imagen en {rect}")
                        
                    except Exception as e:
                        print(f"  ⚠ No se pudo eliminar imagen: {e}")
                        
            except Exception as e:
                print(f"  ✗ Error eliminando elemento: {e}")
                continue
        
        return removed_count
    
    def process_pdf(self, input_path: str, output_path: str) -> dict:
        """
        Procesa un PDF completo eliminando logos de PERSEO
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"No se encontró el archivo: {input_path}")
        
        stats = {
            'pages_processed': 0,
            'elements_removed': 0,
            'pages_with_perseo': 0
        }
        
        try:
            # Abrir el documento
            doc = fitz.open(input_path)
            print(f"Procesando: {input_path}")
            print(f"Páginas totales: {len(doc)}")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                print(f"\nProcesando página {page_num + 1}...")
                
                # Detectar elementos de PERSEO
                perseo_elements = self.detect_perseo_elements(page)
                
                if perseo_elements:
                    print(f"  Encontrados {len(perseo_elements)} elementos PERSEO:")
                    for elem in perseo_elements:
                        print(f"    - {elem['description']}")
                    
                    # Eliminar elementos encontrados
                    removed = self.remove_perseo_elements(page, perseo_elements)
                    stats['elements_removed'] += removed
                    stats['pages_with_perseo'] += 1
                else:
                    print("  No se encontraron elementos PERSEO")
                
                stats['pages_processed'] += 1
            
            # Guardar el documento modificado
            doc.save(output_path)
            doc.close()
            
            print(f"\n✅ Procesamiento completado!")
            print(f"   Archivo guardado en: {output_path}")
            
        except Exception as e:
            print(f"❌ Error procesando PDF: {e}")
            raise
        
        return stats
    
    def process_multiple_pdfs(self, input_folder: str, output_folder: str) -> dict:
        """
        Procesa múltiples PDFs en una carpeta
        """
        if not os.path.exists(input_folder):
            raise FileNotFoundError(f"No se encontró la carpeta: {input_folder}")
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        total_stats = {
            'files_processed': 0,
            'pages_processed': 0,
            'elements_removed': 0,
            'pages_with_perseo': 0,
            'errors': []
        }
        
        # Buscar archivos PDF
        pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
        
        print(f"Encontrados {len(pdf_files)} archivos PDF para procesar")
        
        for pdf_file in pdf_files:
            input_path = os.path.join(input_folder, pdf_file)
            output_path = os.path.join(output_folder, f"limpio_{pdf_file}")
            
            try:
                stats = self.process_pdf(input_path, output_path)
                total_stats['files_processed'] += 1
                total_stats['pages_processed'] += stats['pages_processed']
                total_stats['elements_removed'] += stats['elements_removed']
                total_stats['pages_with_perseo'] += stats['pages_with_perseo']
                
            except Exception as e:
                error_msg = f"Error en {pdf_file}: {str(e)}"
                total_stats['errors'].append(error_msg)
                print(f"❌ {error_msg}")
        
        return total_stats


def limpiar_perseo_pdf_bytes(pdf_bytes: bytes) -> bytes:
    """
    Recibe un PDF en bytes, elimina el logo PERSEO en cada página y retorna el PDF limpio en bytes.
    """
    remover = PerseoLogoRemover()
    input_stream = io.BytesIO(pdf_bytes)
    doc = fitz.open(stream=input_stream, filetype='pdf')
    for page_num in range(len(doc)):
        page = doc[page_num]
        perseo_elements = remover.detect_perseo_elements(page)
        if perseo_elements:
            remover.remove_perseo_elements(page, perseo_elements)
    output_stream = io.BytesIO()
    doc.save(output_stream)
    doc.close()
    return output_stream.getvalue()


def main():
    """Función principal del script"""
    
    # Crear instancia del removedor
    remover = PerseoLogoRemover()
    
    # Ejemplo de uso
    if len(sys.argv) < 2:
        print("Uso del script:")
        print("  python perseo_remover.py archivo.pdf")
        print("  python perseo_remover.py carpeta_input carpeta_output")
        return
    
    try:
        if len(sys.argv) == 2:
            # Procesar un solo archivo
            input_file = sys.argv[1]
            output_file = f"limpio_{os.path.basename(input_file)}"
            
            stats = remover.process_pdf(input_file, output_file)
            
            print(f"\n📊 Estadísticas finales:")
            print(f"   Páginas procesadas: {stats['pages_processed']}")
            print(f"   Páginas con PERSEO: {stats['pages_with_perseo']}")
            print(f"   Elementos eliminados: {stats['elements_removed']}")
            
        elif len(sys.argv) == 3:
            # Procesar carpeta completa
            input_folder = sys.argv[1]
            output_folder = sys.argv[2]
            
            stats = remover.process_multiple_pdfs(input_folder, output_folder)
            
            print(f"\n📊 Estadísticas finales:")
            print(f"   Archivos procesados: {stats['files_processed']}")
            print(f"   Páginas procesadas: {stats['pages_processed']}")
            print(f"   Páginas con PERSEO: {stats['pages_with_perseo']}")
            print(f"   Elementos eliminados: {stats['elements_removed']}")
            
            if stats['errors']:
                print(f"   Errores: {len(stats['errors'])}")
                for error in stats['errors']:
                    print(f"     - {error}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())