import { createContext, useContext, useEffect, useRef } from 'react'
import { Node } from '@tiptap/core'
import { EditorContent, NodeViewWrapper, ReactNodeViewRenderer, useEditor, useEditorState } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { versDoc, versTexte } from '../../utils/editeurDoc.js'

// Visual editor of a news post: what the artisane sees is what the site shows (bold is bold, a heading
// is a heading, a photo is a picture). Only what the site can display is offered. The text is stored
// with light marks (utils/editeurDoc.js converts both ways).

const PhotosContexte = createContext([])

function VuePhoto({ node, selected }) {
  const photos = useContext(PhotosContexte)
  const numero = node.attrs.numero
  const photo = photos[numero - 1]
  return (
    <NodeViewWrapper className={`editeur-photo${selected ? ' editeur-photo--choisie' : ''}`} data-drag-handle>
      {photo ? <img src={photo.url} alt="" /> : <span className="editeur-photo__manque">Cette photo a été retirée</span>}
      <span className="editeur-photo__legende">Photo {numero}{photo?.legende ? ` · ${photo.legende}` : ''}</span>
    </NodeViewWrapper>
  )
}

// [photo n] of the stored text: a block the artisane can move (drag) or delete like a paragraph.
const NoeudPhoto = Node.create({
  name: 'photo',
  group: 'block',
  atom: true,
  draggable: true,
  addAttributes() {
    return { numero: { default: 1 } }
  },
  parseHTML() {
    return [{ tag: 'figure[data-photo]', getAttrs: (el) => ({ numero: Number(el.getAttribute('data-photo')) }) }]
  },
  renderHTML({ HTMLAttributes }) {
    return ['figure', { 'data-photo': HTMLAttributes.numero }]
  },
  addNodeView() {
    return ReactNodeViewRenderer(VuePhoto)
  },
})

const EXTENSIONS = [
  StarterKit.configure({
    heading: { levels: [2] },
    blockquote: false,
    code: false,
    codeBlock: false,
    horizontalRule: false,
    orderedList: false,
    strike: false,
    underline: false,
    link: { openOnClick: false, autolink: true, defaultProtocol: 'https' },
  }),
  NoeudPhoto,
]

const LIEN_VALIDE = /^(https?:\/\/|mailto:)\S+$/

function Bouton({ actif, onClick, children, titre }) {
  return (
    <button
      type="button"
      className={`bouton bouton--discret${actif ? ' bouton--actif' : ''}`}
      aria-pressed={actif}
      title={titre}
      // Keeps the selection in the text while the button is pressed.
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
    >
      {children}
    </button>
  )
}

export default function EditeurTexte({ valeur, onChange, photos }) {
  const rappel = useRef(onChange)
  useEffect(() => {
    rappel.current = onChange
  }, [onChange])

  const editeur = useEditor({
    extensions: EXTENSIONS,
    content: versDoc(valeur),
    onUpdate: ({ editor }) => rappel.current(versTexte(editor.getJSON())),
    editorProps: { attributes: { class: 'editeur-visuel__zone actu__texte', 'aria-label': 'Texte de l’actualité' } },
  })

  const etat = useEditorState({
    editor: editeur,
    selector: ({ editor }) => ({
      titre: editor?.isActive('heading', { level: 2 }) ?? false,
      gras: editor?.isActive('bold') ?? false,
      italique: editor?.isActive('italic') ?? false,
      liste: editor?.isActive('bulletList') ?? false,
      lien: editor?.isActive('link') ?? false,
    }),
  })

  if (!editeur) return null

  function lien() {
    if (etat.lien) {
      editeur.chain().focus().extendMarkRange('link').unsetLink().run()
      return
    }
    const adresse = window.prompt('Adresse du lien (https://…) :', 'https://')
    if (adresse === null) return
    const href = adresse.trim()
    if (!LIEN_VALIDE.test(href)) {
      window.alert('Adresse non valable : elle doit commencer par https:// (ou mailto: pour un e-mail).')
      return
    }
    const { empty } = editeur.state.selection
    if (empty) {
      editeur.chain().focus().insertContent({ type: 'text', text: href, marks: [{ type: 'link', attrs: { href } }] }).run()
    } else {
      editeur.chain().focus().extendMarkRange('link').setLink({ href }).run()
    }
  }

  return (
    <PhotosContexte.Provider value={photos}>
      <div className="editeur-visuel">
        <div className="editeur-texte__barre" role="toolbar" aria-label="Mise en forme">
          <Bouton actif={etat.titre} titre="Intertitre" onClick={() => editeur.chain().focus().toggleHeading({ level: 2 }).run()}>Intertitre</Bouton>
          <Bouton actif={etat.gras} titre="Gras (Ctrl+B)" onClick={() => editeur.chain().focus().toggleBold().run()}><strong>Gras</strong></Bouton>
          <Bouton actif={etat.italique} titre="Italique (Ctrl+I)" onClick={() => editeur.chain().focus().toggleItalic().run()}><em>Italique</em></Bouton>
          <Bouton actif={etat.liste} titre="Liste à puces" onClick={() => editeur.chain().focus().toggleBulletList().run()}>Liste</Bouton>
          <Bouton actif={etat.lien} titre={etat.lien ? 'Retirer le lien' : 'Ajouter un lien'} onClick={lien}>{etat.lien ? 'Retirer le lien' : 'Lien'}</Bouton>
          {photos.length > 0 && (
            <select
              aria-label="Insérer une photo dans le texte"
              value=""
              onChange={(e) => {
                const numero = Number(e.target.value)
                if (numero) editeur.chain().focus().insertContent({ type: 'photo', attrs: { numero } }).run()
              }}
            >
              <option value="">Insérer une photo…</option>
              {photos.map((p, i) => <option key={p.id} value={i + 1}>Photo {i + 1}{p.legende ? ` (${p.legende})` : ''}</option>)}
            </select>
          )}
        </div>
        <EditorContent editor={editeur} />
      </div>
    </PhotosContexte.Provider>
  )
}
